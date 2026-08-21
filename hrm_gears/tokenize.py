"""Token schemes from the upstream dataset builders, used for smoke inputs.

These encodings are copied from Sapient's dataset scripts so a forward
pass can be constructed without materialising the full training corpora.

Sudoku (`dataset/build_sudoku_dataset.py`):
    cell in {0..9}  ->  token = cell + 1
    PAD = 0, vocab = 11, seq = 81

Maze (`dataset/build_maze_dataset.py`):
    charset "# SGo"  ->  tokens 1..5
    PAD = 0, vocab = 6, seq = 900 (30x30)

ARC (`dataset/build_arc_dataset.py`):
    PAD = 0, EOS = 1, colours 0..9 -> tokens 2..11
    vocab = 12, seq = 900 (30x30 padded)
"""

from __future__ import annotations

import torch

MAZE_CHARSET = "# SGo"
ARC_MAX = 30

# Classic easy Sudoku. 0 = blank. Not part of the official 1k-extreme set;
# used only to exercise the ACT loop on a well-posed 9x9 instance.
SAMPLE_SUDOKU = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


def encode_sudoku(grid: list[list[int]] | None = None) -> torch.Tensor:
    source = SAMPLE_SUDOKU if grid is None else grid
    flat = torch.tensor(source, dtype=torch.int32).reshape(1, 81)
    if torch.any((flat < 0) | (flat > 9)):
        raise ValueError("Sudoku cells must be in 0..9 (0 = blank)")
    return flat + 1


def decode_sudoku(tokens: torch.Tensor) -> list[list[int]]:
    values = (tokens.detach().cpu().reshape(9, 9) - 1).tolist()
    return [[int(cell) for cell in row] for row in values]


def encode_maze() -> torch.Tensor:
    """Bordered 30x30 maze with S/G and a snaking open corridor."""
    char2id = {ch: i + 1 for i, ch in enumerate(MAZE_CHARSET)}
    grid = [["#"] * 30 for _ in range(30)]
    for row in range(1, 29):
        if row % 2 == 1:
            for col in range(1, 29):
                grid[row][col] = " "
        else:
            for col in range(1, 29):
                grid[row][col] = "#"
            grid[row][28 if (row // 2) % 2 == 0 else 1] = " "
    grid[1][1] = "S"
    grid[28][28] = "G"
    tokens = [char2id[grid[row][col]] for row in range(30) for col in range(30)]
    return torch.tensor(tokens, dtype=torch.int32).unsqueeze(0)


def encode_arc() -> torch.Tensor:
    """3x3 colour grid, translationally padded the way ARC-HRM expects."""
    inp = torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=torch.int32)
    nrow, ncol = inp.shape
    grid = torch.zeros((ARC_MAX, ARC_MAX), dtype=torch.int32)
    grid[:nrow, :ncol] = inp + 2
    if nrow < ARC_MAX:
        grid[nrow, :ncol] = 1
    if ncol < ARC_MAX:
        grid[:nrow, ncol] = 1
    return grid.reshape(1, ARC_MAX * ARC_MAX)


def make_batch(inputs: torch.Tensor, device: torch.device) -> dict[str, torch.Tensor]:
    return {
        "inputs": inputs.to(device),
        "labels": inputs.clone().to(device),
        "puzzle_identifiers": torch.zeros((1,), dtype=torch.int32, device=device),
    }
