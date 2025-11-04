#!/usr/bin/env python3
"""
KaniTTS Fine-tuning Script
For Botan Voice Model Training
"""

import os
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import torch
import torchaudio
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    TrainerCallback,
)
from transformers.trainer_utils import get_last_checkpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finetune.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AudioTextDataset(Dataset):
    """Dataset for audio-text pairs"""

    def __init__(
        self,
        data_dir: str,
        tokenizer,
        sample_rate: int = 22050,
        max_audio_length: float = 10.0
    ):
        self.data_dir = Path(data_dir)
        self.tokenizer = tokenizer
        self.sample_rate = sample_rate
        self.max_audio_length = max_audio_length

        # Load dataset manifest
        manifest_path = self.data_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            self.data = [json.loads(line) for line in f]

        logger.info(f"Loaded {len(self.data)} samples from {data_dir}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Load audio
        audio_path = self.data_dir / item['audio_filepath']
        waveform, sr = torchaudio.load(audio_path)

        # Resample if necessary
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Trim or pad to max_audio_length
        max_samples = int(self.max_audio_length * self.sample_rate)
        if waveform.shape[1] > max_samples:
            waveform = waveform[:, :max_samples]
        elif waveform.shape[1] < max_samples:
            padding = max_samples - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))

        # Tokenize text
        text = item['text']
        tokens = self.tokenizer(
            text,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt'
        )

        return {
            'input_ids': tokens['input_ids'].squeeze(),
            'attention_mask': tokens['attention_mask'].squeeze(),
            'audio': waveform.squeeze(),
            'text': text
        }


class ProgressCallback(TrainerCallback):
    """Callback for logging training progress"""

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            logger.info(f"Step {state.global_step}: {logs}")


def prepare_data_manifest(
    audio_dir: str,
    text_file: str,
    output_file: str
):
    """
    Prepare manifest.json from audio files and corresponding text file

    Expected structure:
    - audio_dir/: Contains WAV files (e.g., botan_001.wav, botan_002.wav, ...)
    - text_file: Contains corresponding text (one line per audio file)

    Each line in manifest.json:
    {"audio_filepath": "botan_001.wav", "text": "対応するテキスト", "duration": 3.5}
    """
    audio_dir = Path(audio_dir)
    audio_files = sorted(audio_dir.glob("*.wav"))

    with open(text_file, 'r', encoding='utf-8') as f:
        texts = [line.strip() for line in f if line.strip()]

    if len(audio_files) != len(texts):
        raise ValueError(
            f"Mismatch: {len(audio_files)} audio files, {len(texts)} text lines"
        )

    manifest = []
    for audio_path, text in zip(audio_files, texts):
        # Get audio duration
        waveform, sr = torchaudio.load(audio_path)
        duration = waveform.shape[1] / sr

        manifest.append({
            "audio_filepath": audio_path.name,
            "text": text,
            "duration": duration
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in manifest:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    logger.info(f"Created manifest with {len(manifest)} items: {output_file}")
    return manifest


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_training_args(config: Dict) -> TrainingArguments:
    """Setup training arguments from config"""
    training_config = config['training']

    return TrainingArguments(
        output_dir=training_config['output_dir'],
        num_train_epochs=training_config['num_train_epochs'],
        per_device_train_batch_size=training_config['per_device_train_batch_size'],
        per_device_eval_batch_size=training_config['per_device_eval_batch_size'],
        gradient_accumulation_steps=training_config['gradient_accumulation_steps'],
        learning_rate=training_config['learning_rate'],
        weight_decay=training_config['weight_decay'],
        warmup_steps=training_config['warmup_steps'],
        logging_dir=config['logging']['logging_dir'],
        logging_steps=training_config['logging_steps'],
        logging_first_step=config['logging']['logging_first_step'],
        save_steps=training_config['save_steps'],
        eval_steps=training_config['eval_steps'],
        save_total_limit=training_config['save_total_limit'],
        fp16=training_config['fp16'],
        dataloader_num_workers=training_config['dataloader_num_workers'],
        report_to=config['logging']['report_to'],
        load_best_model_at_end=True,
        metric_for_best_model='eval_loss',
        greater_is_better=False,
    )


def main():
    parser = argparse.ArgumentParser(description='Fine-tune KaniTTS model')
    parser.add_argument(
        '--config',
        type=str,
        default='train_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--prepare-data',
        action='store_true',
        help='Prepare data manifest before training'
    )
    parser.add_argument(
        '--audio-dir',
        type=str,
        help='Directory containing audio files (for --prepare-data)'
    )
    parser.add_argument(
        '--text-file',
        type=str,
        help='Text file with transcriptions (for --prepare-data)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    logger.info(f"Loaded configuration from {args.config}")

    # Prepare data if requested
    if args.prepare_data:
        if not args.audio_dir or not args.text_file:
            raise ValueError("--audio-dir and --text-file required with --prepare-data")

        train_dir = Path(config['data']['train_data_path'])
        train_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Preparing training data manifest...")
        prepare_data_manifest(
            args.audio_dir,
            args.text_file,
            train_dir / "manifest.json"
        )

        logger.info("Data preparation complete. Run without --prepare-data to train.")
        return

    # Check CUDA availability
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # Load model and tokenizer
    model_name = config['model']['name']
    cache_dir = config['model']['cache_dir']

    logger.info(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        trust_remote_code=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        trust_remote_code=True,
        torch_dtype=torch.float16 if config['training']['fp16'] else torch.float32
    )

    logger.info(f"Model loaded. Parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")

    # Load datasets
    logger.info("Loading datasets...")
    train_dataset = AudioTextDataset(
        config['data']['train_data_path'],
        tokenizer,
        sample_rate=config['data']['sample_rate'],
        max_audio_length=config['data']['max_audio_length']
    )

    eval_dataset = None
    eval_data_path = config['data'].get('eval_data_path')
    if eval_data_path and Path(eval_data_path).exists():
        eval_dataset = AudioTextDataset(
            eval_data_path,
            tokenizer,
            sample_rate=config['data']['sample_rate'],
            max_audio_length=config['data']['max_audio_length']
        )
        logger.info(f"Loaded {len(eval_dataset)} evaluation samples")

    # Setup training arguments
    training_args = setup_training_args(config)

    # Check for checkpoint
    last_checkpoint = None
    if args.resume:
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
        if last_checkpoint:
            logger.info(f"Resuming from checkpoint: {last_checkpoint}")

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        callbacks=[ProgressCallback()],
    )

    # Train
    logger.info("Starting training...")
    logger.info(f"Total epochs: {training_args.num_train_epochs}")
    logger.info(f"Batch size: {training_args.per_device_train_batch_size}")
    logger.info(f"Gradient accumulation: {training_args.gradient_accumulation_steps}")
    logger.info(f"Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")

    train_result = trainer.train(resume_from_checkpoint=last_checkpoint)

    # Save final model
    final_model_path = Path(training_args.output_dir) / "final_model"
    logger.info(f"Saving final model to {final_model_path}")
    trainer.save_model(final_model_path)
    tokenizer.save_pretrained(final_model_path)

    # Save training metrics
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    logger.info("Training complete!")
    logger.info(f"Final loss: {metrics.get('train_loss', 'N/A')}")
    logger.info(f"Model saved to: {final_model_path}")


if __name__ == "__main__":
    main()
