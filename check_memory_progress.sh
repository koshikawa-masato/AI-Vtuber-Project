#!/bin/bash
# Check memory generation progress

echo "=== Memory Generation Progress ==="
echo ""

# Check process status
if ps -p 19595 > /dev/null 2>&1; then
    echo "[STATUS] Process 19595 is running"
else
    echo "[STATUS] Process 19595 has finished"
fi

echo ""

# Count memories in database
echo "[DATABASE] Current memory count:"
python3 -c "
import sqlite3
conn = sqlite3.connect('sisters_memory.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM botan_memories')
count = cursor.fetchone()[0]
print(f'  Total memories: {count}/98')
conn.close()
"

echo ""

# Show last 20 lines of log
echo "[LOG] Last 20 lines:"
echo "---"
tail -20 /home/koshikawa/toExecUnit/phase_d_memory_generation.log
echo "---"
