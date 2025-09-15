import sys
from pathlib import Path

# プロジェクトルートをパスへ追加して `import app` を可能に
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 将来的に共通フィクスチャをここへ追加可能
