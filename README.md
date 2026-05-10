# LNO Calculator

Battery material synthesis calculation tool with interactive GUI.

## Features
- **Tab ①  Ni Precursor** — Calculate how much Ni-source precursor to add to spent powder to reach a target Ni%
- **Tab ②  Li Source**    — Calculate how much Li-source (e.g. LiOH·H₂O) to add per batch
- **Formula Tool**         — Parse any chemical formula and get element breakdown + molar mass

## Supported Formula Syntax
| Example | Meaning |
|---|---|
| `Li0.7Ni0.63Co0.15Mn0.19O2` | standard fractional formula |
| `Ni(OH)1.84(FBrSI)0.04` | parenthetical groups with float coefficient |
| `LiOH*H2O` or `LiOH·H2O` | hydrate notation |
| `Li2CO3` | integer stoichiometry |

## Installation & Running

### Option A — Run directly (no install needed)
```bash
cd LNOcalculation
python LNOcalculation.py
```

### Option B — Install command so you can type `LNOcalculation` anywhere
```bash
cd LNOcalculation
python setup.py install
```
Then from any terminal:
```bash
LNOcalculation
```

### Option C — Conda environment
```bash
# Create/activate your env first
conda activate your_env

# Install the command into that env
cd LNOcalculation
python setup.py install

# Now in that env you can run:
LNOcalculation
```

### Uninstall
```bash
python setup.py uninstall
```

## Requirements
- Python 3.7+
- `tkinter` (included with standard Python / Anaconda)
- No additional pip packages needed

## File Structure
```
LNOcalculation/
├── LNOcalculation.py    ← entry point (run this)
├── lno_gui.py           ← GUI code
├── lno_calculator.py    ← calculation engine
├── setup.py             ← install/uninstall command
└── README.md
```

## Workflow

1. **Tab ①**: Enter spent powder formula, precursor formula, target Ni%, and either spent or precursor mass → click **Calculate Precursor**
2. **Tab ②**: Enter Li source formula, target Li/Ni ratio, and desired Ni-rich batch mass → click **Calculate Li Source**
3. **Formula Tool**: Verify any formula parses correctly before using it in calculations
