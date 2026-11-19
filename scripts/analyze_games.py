#!/usr/bin/env python3
"""Analyse le corpus PGN local et un échantillon au moteur.

Lecture seule : ce script n'appelle pas Chess.com. Les seuils et la sélection
sont décrits dans AGENTS.md. Les évaluations viennent de Stockfish.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import chess
import chess.engine
import chess.pgn

ROOT = Path(__file__).resolve().parents[1]
BRUSSELS = ZoneInfo("Europe/Brussels")
USER = "zoliandru"

VAL = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}
def self_test() -> None:
    queen = chess.Board("4k3/8/8/8/8/8/5n2/4K2Q w - - 0 1")
    flipped = with_opponent_to_move(queen, chess.WHITE)
    assert flipped is not None
    gain, _san = capture_swing(flipped, chess.WHITE)
    assert gain >= 9, gain

    trade = chess.Board("4k3/8/8/8/1b6/2N5/3P4/4K3 b - - 0 1")
    gain, _san = capture_swing(trade, chess.WHITE)
    assert gain == 0, gain

    pawn_takes = chess.Board("4k3/8/8/8/1p6/2N5/3P4/4K3 b - - 0 1")
    gain, _san = capture_swing(pawn_takes, chess.WHITE)
    assert gain == 2, gain

    safe = chess.Board("4k3/8/8/8/8/2N5/8/4K3 b - - 0 1")
    gain, _san = capture_swing(safe, chess.WHITE)
    assert gain == 0, gain

    loose = chess.Board("4k3/8/8/8/1p6/8/8/1N2K3 w - - 0 1")
    event = move_material_loss(loose, chess.Move.from_uci("b1c3"), chess.WHITE)
    assert event["loss"] == 3, event

    wins_queen = chess.Board("4k3/8/8/3q4/8/2N5/8/4K3 w - - 0 1")
    event = move_material_loss(wins_queen, chess.Move.from_uci("c3d5"), chess.WHITE)
    assert event["loss"] <= 0, event

    knight_for_pawn = chess.Board("3qk3/8/8/3p4/8/2N5/8/4K3 w - - 0 1")
    event = move_material_loss(knight_for_pawn, chess.Move.from_uci("c3d5"), chess.WHITE)
    assert event["loss"] == 2, event


def with_opponent_to_move(board: chess.Board, us_color: chess.Color) -> chess.Board | None:
    """Copie où l'adversaire est au trait, ou None si cette copie est illégale."""
    opponent = not us_color
    if board.turn == opponent:
        return board.copy(stack=False)
    if board.is_check():
        return None
    scratch = board.copy(stack=False)
    scratch.ep_square = None
    scratch.turn = opponent
    king = scratch.king(us_color)
    if king is not None and scratch.is_attacked_by(opponent, king):
        return None
    return scratch


def capture_swing(board: chess.Board, us_color: chess.Color) -> tuple[int, str | None]:
    """Gain matériel maximal de l'adversaire, déjà au trait, en une capture plus une reprise.

    Le gain est en points (pion 1, cavalier ou fou 3, tour 5, dame 9).
    On suppose que nous rejouons la reprise la moins mauvaise sur la case d'arrivée.
    """
    if board.turn == us_color:
        raise ValueError("l'adversaire doit être au trait")
    current = material(board, us_color) - material(board, not us_color)
    worst = current
    worst_san: str | None = None
    for move in list(board.legal_moves):
        if not board.is_capture(move):
            continue
        san = board.san(move)
        board.push(move)
        landing = move.to_square
        best_for_us = material(board, us_color) - material(board, not us_color)
        if not board.is_game_over():
            for reply in board.generate_legal_moves(to_mask=chess.BB_SQUARES[landing]):
                if not board.is_capture(reply):
                    continue
                board.push(reply)
                best_for_us = max(best_for_us, material(board, us_color) - material(board, not us_color))
                board.pop()
        board.pop()
        if best_for_us < worst:
            worst = best_for_us
            worst_san = san
    return current - worst, worst_san


def move_material_loss(board: chess.Board, move: chess.Move, us_color: chess.Color) -> dict:
    """Perte nette créée par `move`, face à la meilleure capture adverse en un coup.

    `loss` compare le bilan déjà disponible avant le coup au bilan après le coup.
    Un échange égal vaut 0. Un cavalier qui prend un pion et se fait reprendre vaut 2.
    Une dame gagnée vaut une perte négative.
    """
    diff_before = material(board, us_color) - material(board, not us_color)
    counterfactual = with_opponent_to_move(board, us_color)
    if counterfactual is None:
        gain_before = 0
    else:
        gain_before, _before_san = capture_swing(counterfactual, us_color)
    scratch = board.copy(stack=False)
    scratch.push(move)
    if scratch.is_game_over() and not scratch.is_checkmate():
        gain_after, punish_san = 0, None
    elif scratch.turn == us_color:
        gain_after, punish_san = 0, None
    else:
        gain_after, punish_san = capture_swing(scratch, us_color)
    diff_after = material(scratch, us_color) - material(scratch, not us_color)
    outcome_before = diff_before - gain_before
    outcome_after = diff_after - gain_after
    loss = outcome_before - outcome_after
    return {
        "loss": loss,
        "punish_san": punish_san if loss >= 1 else None,
        "gain_before": gain_before,
        "gain_after": gain_after,
        "ignored": gain_before >= 2 and gain_after >= 2 and 0 <= loss < 2,
    }


def loss_bucket(loss: int) -> str:
    if loss >= 9:
        return "9+"
    if loss >= 5:
        return "5-8"
    if loss >= 3:
        return "3-4"
    if loss >= 2:
        return "2"
    return "1"


def material(board: chess.Board, color: chess.Color) -> int:
    total = 0
    for piece in board.piece_map().values():
        if piece.color == color and piece.piece_type != chess.KING:
            total += VAL[piece.piece_type]
    return total


def phase_of(board: chess.Board) -> str:
    total = 0
    queens = 0
    for piece in board.piece_map().values():
        if piece.piece_type == chess.KING:
            continue
        total += VAL[piece.piece_type]
        if piece.piece_type == chess.QUEEN:
            queens += 1
    if (queens == 0 and total <= 20) or total <= 13:
        return "finale"
    if board.fullmove_number <= 12:
        return "ouverture"
    return "milieu"


def parse_tc(time_control: str) -> tuple[int, int] | None:
    if not time_control or "/" in time_control:
        return None
    if "+" in time_control:
        base_s, inc_s = time_control.split("+", 1)
        return int(base_s), int(inc_s)
    return int(time_control), 0


def infer_time_class(base: int, increment: int) -> str:
    estimate = base + 40 * increment
    if estimate < 180:
        return "bullet"
    if estimate < 600:
        return "blitz"
    if estimate < 1800:
        return "rapid"
    return "classical"


def parse_elo(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def end_datetime(headers: chess.pgn.Headers) -> datetime | None:
    date = headers.get("EndDate") or headers.get("UTCDate") or headers.get("Date")
    clock = headers.get("EndTime") or headers.get("UTCTime") or "00:00:00"
    if not date:
        return None
    try:
        return datetime.strptime(f"{date} {clock}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def our_result(result: str, color: chess.Color) -> str | None:
    if result == "1/2-1/2":
        return "draw"
    if result == "1-0":
        return "win" if color == chess.WHITE else "loss"
    if result == "0-1":
        return "loss" if color == chess.WHITE else "win"
    return None


def expected_score(own: int, opp: int) -> float:
    return 1 / (1 + 10 ** ((opp - own) / 400))


def eco_family(headers: chess.pgn.Headers) -> str:
    url = headers.get("ECOUrl", "")
    if "/openings/" in url:
        name = url.split("/openings/", 1)[1].split("...")[0]
        return name.replace("-", " ").strip() or headers.get("ECO", "?")
    return headers.get("ECO", "?") or "?"


def format_line(sans: list[str], plies: int = 6) -> str:
    bits: list[str] = []
    for index, san in enumerate(sans[:plies]):
        if index % 2 == 0:
            bits.append(f"{index // 2 + 1}.{san}")
        else:
            bits.append(san)
    return " ".join(bits)


def termination_bucket(termination: str, result: str | None) -> str:
    text = (termination or "").lower()
    if result == "draw":
        if "repetition" in text:
            return "nulle_repetition"
        if "stalemate" in text:
            return "nulle_pat"
        if "insufficient" in text:
            return "nulle_materiel"
        if "agreement" in text:
            return "nulle_accord"
        if "50" in text:
            return "nulle_cinquante"
        if "time" in text:
            return "nulle_temps"
        return "nulle_autre"
    if "checkmate" in text:
        how = "mat"
    elif "resign" in text:
        how = "resignation"
    elif "abandon" in text:
        how = "deconnexion"
    elif "time" in text:
        how = "temps"
    else:
        how = "autre"
    if result == "win":
        return f"gain_{how}"
    if result == "loss":
        return f"perte_{how}"
    return how


def score_value(result: str | None) -> float | None:
    return {"win": 1.0, "draw": 0.5, "loss": 0.0}.get(result or "")


def median(values: list[float]) -> float | None:
    clean = sorted(value for value in values if value is not None)
    if not clean:
        return None
    mid = len(clean) // 2
    if len(clean) % 2:
        return float(clean[mid])
    return float(clean[mid - 1] + clean[mid]) / 2


def mean(values: list[float]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return float(statistics.fmean(clean))


def round_or_none(value: float | None, digits: int = 3) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def format_punish(loss: int, punish_san: str | None) -> str | None:
    if loss < 1 or not punish_san:
        return None
    return f"{punish_san} gagne {loss} points de matériel (pion 1, pièce mineure 3, tour 5, dame 9)."


def load_games(pgn_dir: Path) -> list[chess.pgn.Game]:
    games: list[chess.pgn.Game] = []
    for path in sorted(pgn_dir.glob("*.pgn")):
        with path.open(encoding="utf-8") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                games.append(game)
    return games


def walk_game(game: chess.pgn.Game) -> dict | None:
    headers = game.headers
    white = headers.get("White", "")
    black = headers.get("Black", "")
    if white.lower() == USER:
        color = chess.WHITE
    elif black.lower() == USER:
        color = chess.BLACK
    else:
        return None
    result = our_result(headers.get("Result", ""), color)
    tc = parse_tc(headers.get("TimeControl", ""))
    if tc is None:
        return {"skip": "cadence_non_live"}
    base, increment = tc
    time_class = headers.get("TimeClass") or infer_time_class(base, increment)
    rules = headers.get("Rules") or "chess"
    if rules != "chess":
        return {"skip": f"regles_{rules}"}
    if time_class not in {"blitz", "rapid"}:
        return {"skip": f"classe_{time_class}"}
    board = game.board()
    if board.fen() != chess.STARTING_FEN:
        return {"skip": "position_initiale"}
    if result is None:
        return {"skip": "resultat_inconnu"}

    when = end_datetime(headers)
    if when is None:
        return {"skip": "date"}
    local = when.astimezone(BRUSSELS)
    iso = local.isocalendar()
    our_elo = parse_elo(headers.get("WhiteElo" if color == chess.WHITE else "BlackElo"))
    opp_elo = parse_elo(headers.get("BlackElo" if color == chess.WHITE else "WhiteElo"))

    sans: list[str] = []
    prev_clock = {chess.WHITE: float(base), chess.BLACK: float(base)}
    new_piece_hangs = 0
    full_piece_hangs = 0
    new_pawn_hangs = 0
    ignored_piece_hangs = 0
    opening_piece_hangs = 0
    hangs_low_clock = 0
    hangs_with_time = 0
    hang_pieces: Counter[str] = Counter()
    hang_phases: Counter[str] = Counter()
    first_piece_hang_move = None
    opening_moves = 0
    opening_fast = 0
    opening_spent: list[float] = []
    middlegame_spent: list[float] = []
    reached_10 = False
    reached_20 = False
    min_clock = None
    castled = False
    castle_move = None
    queen_early = 0
    reached_15 = False
    king_unCastled_center_15 = False
    max_adv = 0
    min_adv = 0
    first_swing_3 = None
    first_swing_5 = None
    pending_diff = None
    pending_move = None
    plies = 0

    for node in game.mainline():
        move = node.move
        if move is None:
            break
        mover = board.turn
        fullmove = board.fullmove_number
        clock_after = node.clock()
        clock_before = prev_clock.get(mover)
        san = board.san(move)
        sans.append(san)
        castling = board.is_castling(move)
        moved_piece = board.piece_at(move.from_square)
        current_phase = phase_of(board)
        material_event = move_material_loss(board, move, color) if mover == color else None
        board.push(move)
        plies += 1
        # Un avantage ne compte qu'une fois la réponse adverse passée.
        # Sinon la prise d'une dame reprise au coup suivant est un faux « +9 ».
        current_diff = material(board, color) - material(board, not color)
        if pending_diff is not None and not board.is_game_over():
            if first_swing_3 is None and pending_diff >= 3 and current_diff >= 3:
                first_swing_3 = {"side": "us", "move": pending_move, "diff": pending_diff}
            elif first_swing_3 is None and pending_diff <= -3 and current_diff <= -3:
                first_swing_3 = {"side": "them", "move": pending_move, "diff": pending_diff}
            if first_swing_5 is None and pending_diff >= 5 and current_diff >= 5:
                first_swing_5 = {"side": "us", "move": pending_move, "diff": pending_diff}
            elif first_swing_5 is None and pending_diff <= -5 and current_diff <= -5:
                first_swing_5 = {"side": "them", "move": pending_move, "diff": pending_diff}
            if abs(pending_diff) >= 3 and abs(current_diff) >= 3 and pending_diff * current_diff > 0:
                max_adv = max(max_adv, pending_diff)
                min_adv = min(min_adv, pending_diff)
        pending_diff = current_diff
        pending_move = fullmove

        if mover == color:
            if castling:
                castled = True
                castle_move = fullmove
            if moved_piece and moved_piece.piece_type == chess.QUEEN and fullmove <= 8:
                queen_early += 1
            spent = None
            if clock_before is not None and clock_after is not None:
                spent = clock_before + increment - clock_after
                if spent < -1 or spent > base + increment + 30:
                    spent = None
            if clock_before is not None:
                min_clock = clock_before if min_clock is None else min(min_clock, clock_before)
                if clock_before < 10:
                    reached_10 = True
                if clock_before < 20:
                    reached_20 = True
            if fullmove <= 8:
                opening_moves += 1
                if spent is not None:
                    opening_spent.append(spent)
                    if spent < 2:
                        opening_fast += 1
            elif 15 <= fullmove <= 30 and spent is not None:
                middlegame_spent.append(spent)

            if material_event is not None:
                loss = int(material_event["loss"])
                low_clock = clock_before is not None and clock_before < 20
                if loss == 1:
                    new_pawn_hangs += 1
                elif loss >= 2:
                    new_piece_hangs += 1
                    hang_pieces[loss_bucket(loss)] += 1
                    hang_phases[current_phase] += 1
                    if first_piece_hang_move is None:
                        first_piece_hang_move = fullmove
                    if fullmove <= 10:
                        opening_piece_hangs += 1
                    if low_clock:
                        hangs_low_clock += 1
                    elif clock_before is not None:
                        hangs_with_time += 1
                    if loss >= 3:
                        full_piece_hangs += 1
                if material_event["ignored"]:
                    ignored_piece_hangs += 1
            if not reached_15 and board.fullmove_number >= 15:
                reached_15 = True
                king_square = board.king(color)
                if king_square is not None and not castled and chess.square_file(king_square) in (3, 4):
                    king_unCastled_center_15 = True
        if clock_after is not None:
            prev_clock[mover] = clock_after

    final_diff = material(board, color) - material(board, not color)
    # Dernière position : plus de réponse possible (mat, abandon dans le PGN, fin de partie).
    if pending_diff is not None:
        if first_swing_3 is None and pending_diff >= 3 and final_diff >= 3:
            first_swing_3 = {"side": "us", "move": pending_move, "diff": pending_diff}
        elif first_swing_3 is None and pending_diff <= -3 and final_diff <= -3:
            first_swing_3 = {"side": "them", "move": pending_move, "diff": pending_diff}
        if first_swing_5 is None and pending_diff >= 5 and final_diff >= 5:
            first_swing_5 = {"side": "us", "move": pending_move, "diff": pending_diff}
        elif first_swing_5 is None and pending_diff <= -5 and final_diff <= -5:
            first_swing_5 = {"side": "them", "move": pending_move, "diff": pending_diff}
    line = format_line(sans, 6) if len(sans) >= 6 else ""
    if color == chess.WHITE:
        first_bucket = f"1.{sans[0]}" if sans else "?"
    else:
        if len(sans) >= 2:
            first_bucket = f"contre {sans[0]} : {sans[1]}"
        elif sans:
            first_bucket = f"contre {sans[0]} : (sans réponse)"
        else:
            first_bucket = "?"

    return {
        "skip": None,
        "url": headers.get("Link", ""),
        "color": "white" if color == chess.WHITE else "black",
        "color_enum": color,
        "result": result,
        "our_elo": our_elo,
        "opp_elo": opp_elo,
        "expected": expected_score(our_elo, opp_elo) if our_elo and opp_elo else None,
        "time_control": headers.get("TimeControl", ""),
        "time_class": time_class,
        "rated": headers.get("Rated", "true") == "true",
        "eco": headers.get("ECO", ""),
        "eco_family": eco_family(headers),
        "line": line,
        "first_bucket": first_bucket,
        "termination": termination_bucket(headers.get("Termination", ""), result),
        "termination_raw": headers.get("Termination", ""),
        "when": local.isoformat(timespec="seconds"),
        "date": local.date().isoformat(),
        "month": local.strftime("%Y-%m"),
        "week": f"{iso.year}-W{iso.week:02d}",
        "plies": plies,
        "castled": castled,
        "castle_move": castle_move,
        "queen_early": queen_early,
        "reached_15": reached_15,
        "king_center_15": king_unCastled_center_15,
        "max_adv": max_adv,
        "min_adv": min_adv,
        "final_diff": final_diff,
        "first_swing_3": first_swing_3,
        "first_swing_5": first_swing_5,
        "new_piece_hangs": new_piece_hangs,
        "full_piece_hangs": full_piece_hangs,
        "new_pawn_hangs": new_pawn_hangs,
        "ignored_piece_hangs": ignored_piece_hangs,
        "opening_piece_hangs": opening_piece_hangs,
        "hangs_low_clock": hangs_low_clock,
        "hangs_with_time": hangs_with_time,
        "hang_pieces": dict(hang_pieces),
        "hang_phases": dict(hang_phases),
        "first_piece_hang_move": first_piece_hang_move,
        "opening_moves": opening_moves,
        "opening_fast": opening_fast,
        "opening_spent_median": median(opening_spent),
        "middlegame_spent_median": median(middlegame_spent),
        "reached_10": reached_10,
        "reached_20": reached_20,
        "min_clock": min_clock,
        "game": game,
    }


def bucket_record(rows: list[dict], key: str) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    table = []
    for name, items in grouped.items():
        scored = [item for item in items if score_value(item["result"]) is not None]
        table.append(
            {
                "name": name,
                "n": len(items),
                "win": sum(item["result"] == "win" for item in items),
                "loss": sum(item["result"] == "loss" for item in items),
                "draw": sum(item["result"] == "draw" for item in items),
                "score": round_or_none(mean([score_value(item["result"]) for item in scored])),
                "avg_our_elo": round_or_none(mean([item["our_elo"] for item in items if item["our_elo"]]), 1),
                "avg_opp_elo": round_or_none(mean([item["opp_elo"] for item in items if item["opp_elo"]]), 1),
            "piece_hangs_per_game": round_or_none(mean([item["new_piece_hangs"] for item in items]), 2),
            "full_piece_per_game": round_or_none(mean([item["full_piece_hangs"] for item in items]), 2),
            "opening_hangs_per_game": round_or_none(mean([item["opening_piece_hangs"] for item in items]), 2),
            }
        )
    table.sort(key=lambda item: (-item["n"], item["name"]))
    return table


def swing_table(rows: list[dict], field: str) -> dict:
    us = [row for row in rows if row[field] and row[field]["side"] == "us"]
    them = [row for row in rows if row[field] and row[field]["side"] == "them"]

    def pack(subset: list[dict]) -> dict:
        return {
            "n": len(subset),
            "score": round_or_none(mean([score_value(row["result"]) for row in subset])),
            "win": sum(row["result"] == "win" for row in subset),
            "loss": sum(row["result"] == "loss" for row in subset),
            "draw": sum(row["result"] == "draw" for row in subset),
            "median_move": median([row[field]["move"] for row in subset]),
        }

    return {"us_first": pack(us), "them_first": pack(them)}


def aggregate_corpus(rows: list[dict]) -> dict:
    scored = [row for row in rows if score_value(row["result"]) is not None]
    by_color = {}
    for color in ("white", "black"):
        subset = [row for row in scored if row["color"] == color]
        by_color[color] = {
            "n": len(subset),
            "win": sum(row["result"] == "win" for row in subset),
            "loss": sum(row["result"] == "loss" for row in subset),
            "draw": sum(row["result"] == "draw" for row in subset),
            "score": round_or_none(mean([score_value(row["result"]) for row in subset])),
            "expected": round_or_none(mean([row["expected"] for row in subset if row["expected"] is not None])),
            "avg_our_elo": round_or_none(mean([row["our_elo"] for row in subset if row["our_elo"]]), 1),
            "avg_opp_elo": round_or_none(mean([row["opp_elo"] for row in subset if row["opp_elo"]]), 1),
        }

    def month_week(field: str) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in scored:
            grouped[row[field]].append(row)
        out = []
        for name in sorted(grouped):
            items = grouped[name]
            elos = [row["our_elo"] for row in items if row["our_elo"]]
            out.append(
                {
                    "name": name,
                    "n": len(items),
                    "score": round_or_none(mean([score_value(row["result"]) for row in items])),
                    "avg_elo": round_or_none(mean(elos), 1),
                    "end_elo": items[-1]["our_elo"],
                }
            )
        return out

    long_games = [row for row in rows if row["plies"] >= 30]
    reached_15 = [row for row in rows if row["reached_15"]]
    wins = [row for row in rows if row["result"] == "win"]
    losses = [row for row in rows if row["result"] == "loss"]

    def hang_pack(subset: list[dict]) -> dict:
        return {
            "n": len(subset),
            "games_with_piece_hang": sum(row["new_piece_hangs"] > 0 for row in subset),
            "piece_hangs_per_game": round_or_none(mean([row["new_piece_hangs"] for row in subset]), 2),
            "full_piece_per_game": round_or_none(mean([row["full_piece_hangs"] for row in subset]), 2),
            "pawn_hangs_per_game": round_or_none(mean([row["new_pawn_hangs"] for row in subset]), 2),
            "ignored_piece_per_game": round_or_none(mean([row["ignored_piece_hangs"] for row in subset]), 2),
            "median_first_piece_hang": median(
                [row["first_piece_hang_move"] for row in subset if row["first_piece_hang_move"]]
            ),
        }

    hang_pieces: Counter[str] = Counter()
    hang_phases: Counter[str] = Counter()
    for row in rows:
        hang_pieces.update(row["hang_pieces"])
        hang_phases.update(row["hang_phases"])

    time_loss_ahead = [
        row
        for row in rows
        if row["termination"] == "perte_temps" and row["final_diff"] >= 3
    ]
    time_loss_piece = [
        row
        for row in rows
        if row["termination"] == "perte_temps" and row["final_diff"] >= 5
    ]

    lines = {}
    for color in ("white", "black"):
        subset = [row for row in rows if row["color"] == color and row["line"]]
        table = bucket_record(subset, "line")
        lines[color] = [item for item in table if item["n"] >= 8][:12]

    low_clock = [row for row in rows if row["reached_10"]]
    no_low_clock = [row for row in rows if not row["reached_10"]]

    return {
        "n": len(rows),
        "rated_n": sum(row["rated"] for row in rows),
        "unrated_n": sum(not row["rated"] for row in rows),
        "date_min": min(row["date"] for row in rows),
        "date_max": max(row["date"] for row in rows),
        "results": {
            "win": sum(row["result"] == "win" for row in rows),
            "loss": sum(row["result"] == "loss" for row in rows),
            "draw": sum(row["result"] == "draw" for row in rows),
            "score": round_or_none(mean([score_value(row["result"]) for row in scored])),
            "expected": round_or_none(mean([row["expected"] for row in rows if row["expected"] is not None])),
        },
        "by_color": by_color,
        "time_controls": dict(Counter(row["time_control"] for row in rows)),
        "time_classes": dict(Counter(row["time_class"] for row in rows)),
        "by_month": month_week("month"),
        "by_week": month_week("week"),
        "elo": {
            "avg": round_or_none(mean([row["our_elo"] for row in rows if row["our_elo"]]), 1),
            "first_30_avg": round_or_none(mean([row["our_elo"] for row in rows[:30] if row["our_elo"]]), 1),
            "last_30_avg": round_or_none(mean([row["our_elo"] for row in rows[-30:] if row["our_elo"]]), 1),
            "min": min((row["our_elo"] for row in rows if row["our_elo"]), default=None),
            "max": max((row["our_elo"] for row in rows if row["our_elo"]), default=None),
            "start": next((row["our_elo"] for row in rows if row["our_elo"]), None),
            "end": next((row["our_elo"] for row in reversed(rows) if row["our_elo"]), None),
            "avg_opp": round_or_none(mean([row["opp_elo"] for row in rows if row["opp_elo"]]), 1),
        },
        "length": {
            "median_plies": median([row["plies"] for row in rows]),
            "median_plies_win": median([row["plies"] for row in wins]),
            "median_plies_loss": median([row["plies"] for row in losses]),
            "under_16_plies": sum(row["plies"] < 16 for row in rows),
            "under_16_losses": sum(row["plies"] < 16 and row["result"] == "loss" for row in rows),
        },
        "terminations": dict(Counter(row["termination"] for row in rows)),
        "time_losses_ahead_3": {
            "n": len(time_loss_ahead),
            "examples": [
                {"url": row["url"], "date": row["date"], "final_diff": row["final_diff"], "color": row["color"]}
                for row in sorted(time_loss_ahead, key=lambda item: -item["final_diff"])[:8]
            ],
        },
        "time_losses_ahead_5": len(time_loss_piece),
        "clock": {
            "reached_under_10s": pack_score(low_clock),
            "never_under_10s": pack_score(no_low_clock),
            "reached_under_20s": sum(row["reached_20"] for row in rows),
            "median_spent_moves_1_8": round_or_none(median([row["opening_spent_median"] for row in rows if row["opening_spent_median"] is not None]), 2),
            "median_spent_moves_15_30": round_or_none(
                median([row["middlegame_spent_median"] for row in rows if row["middlegame_spent_median"] is not None]),
                2,
            ),
            "opening_moves": sum(row["opening_moves"] for row in rows),
            "opening_fast_under_2s": sum(row["opening_fast"] for row in rows),
        },
        "habits": {
            "castled_rate_games_30plies": round_or_none(
                mean([1.0 if row["castled"] else 0.0 for row in long_games])
            ),
            "castled_n": sum(row["castled"] for row in rows),
            "median_castle_move": median([row["castle_move"] for row in rows if row["castle_move"]]),
            "reached_15": len(reached_15),
            "king_center_15_among_reached": sum(row["king_center_15"] for row in reached_15),
            "queen_moved_by_8_rate": round_or_none(
                mean([1.0 if row["queen_early"] else 0.0 for row in rows])
            ),
            "median_queen_early_moves": median([row["queen_early"] for row in rows]),
        },
        "hangs": {
            "all": hang_pack(rows),
            "wins": hang_pack(wins),
            "losses": hang_pack(losses),
            "pieces": dict(hang_pieces),
            "phases": dict(hang_phases),
            "with_at_least_20s": sum(row["hangs_with_time"] for row in rows),
            "under_20s": sum(row["hangs_low_clock"] for row in rows),
        },
        "conversion": {
            "first_swing_3": swing_table(rows, "first_swing_3"),
            "first_swing_5": swing_table(rows, "first_swing_5"),
        },
        "first_buckets": {
            "white": bucket_record([row for row in rows if row["color"] == "white"], "first_bucket"),
            "black": bucket_record([row for row in rows if row["color"] == "black"], "first_bucket"),
        },
        "lines": lines,
        "eco_families": [item for item in bucket_record(rows, "eco_family") if item["n"] >= 10][:15],
    }


def pack_score(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "score": round_or_none(mean([score_value(row["result"]) for row in rows])),
        "win": sum(row["result"] == "win" for row in rows),
        "loss": sum(row["result"] == "loss" for row in rows),
        "draw": sum(row["result"] == "draw" for row in rows),
    }


def select_sample(rows: list[dict], size: int) -> list[dict]:
    eligible = [
        row
        for row in rows
        if row["rated"] and row["time_class"] == "blitz" and row["plies"] >= 16 and row["url"]
    ]
    by_result: dict[str, list[dict]] = {"win": [], "loss": [], "draw": []}
    for row in eligible:
        by_result[row["result"]].append(row)
    for subset in by_result.values():
        subset.sort(key=lambda row: row["when"])
    if not eligible:
        return []
    quotas = largest_remainder({key: len(value) / len(eligible) for key, value in by_result.items()}, size)
    selected: list[dict] = []
    for key, quota in quotas.items():
        selected.extend(take_even(by_result[key], quota))
    # Si un quota dépasse le disponible, take_even rend tout le groupe : on complète.
    if len(selected) < size:
        chosen = {row["url"] for row in selected}
        rest = [row for row in eligible if row["url"] not in chosen]
        rest.sort(key=lambda row: row["when"])
        selected.extend(take_even(rest, size - len(selected)))
    selected.sort(key=lambda row: row["when"])
    return selected[:size]


def largest_remainder(weights: dict[str, float], total: int) -> dict[str, int]:
    raw = {key: weight * total for key, weight in weights.items()}
    floors = {key: int(value) for key, value in raw.items()}
    leftover = total - sum(floors.values())
    order = sorted(raw, key=lambda key: raw[key] - floors[key], reverse=True)
    for key in order[:leftover]:
        floors[key] += 1
    return floors


def take_even(pool: list[dict], count: int) -> list[dict]:
    if count <= 0 or not pool:
        return []
    if count >= len(pool):
        return list(pool)
    picked: list[dict] = []
    seen: set[int] = set()
    for index in range(count):
        cursor = min(len(pool) - 1, int((index + 0.5) * len(pool) / count))
        if cursor not in seen:
            seen.add(cursor)
            picked.append(pool[cursor])
    if len(picked) < count:
        for index, row in enumerate(pool):
            if index not in seen:
                picked.append(row)
                seen.add(index)
            if len(picked) >= count:
                break
    return picked[:count]


def white_cp(score: chess.engine.PovScore) -> int:
    return int(score.white().score(mate_score=100000))


def player_pov(score: int, color: chess.Color) -> int:
    return score if color == chess.WHITE else -score


def pv_san(board: chess.Board, pv: list[chess.Move], limit: int = 4) -> str:
    scratch = board.copy(stack=False)
    names: list[str] = []
    for move in pv[:limit]:
        if move not in scratch.legal_moves:
            break
        names.append(scratch.san(move))
        scratch.push(move)
    return " ".join(names)


def analyze_with_engine(engine: chess.engine.SimpleEngine, row: dict, depth: int) -> dict:
    game: chess.pgn.Game = row["game"]
    color: chess.Color = row["color_enum"]
    headers = game.headers
    tc = parse_tc(headers.get("TimeControl", ""))
    assert tc is not None
    base, increment = tc
    board = game.board()
    prev_clock = {chess.WHITE: float(base), chess.BLACK: float(base)}
    steps = []
    for node in game.mainline():
        move = node.move
        if move is None or board.is_game_over():
            break
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        pv = list(info.get("pv") or [])
        best = pv[0] if pv else None
        steps.append(
            {
                "mover": board.turn,
                "move": move,
                "san": board.san(move),
                "best": best,
                "best_san": board.san(best) if best else None,
                "pv": pv_san(board, pv),
                "score_before": white_cp(info["score"]),
                "fen_before": board.fen(),
                "clock_before": prev_clock.get(board.turn),
                "clock_after": node.clock(),
                "fullmove": board.fullmove_number,
                "phase": phase_of(board),
            }
        )
        mover = board.turn
        board.push(move)
        if node.clock() is not None:
            prev_clock[mover] = node.clock()

    components: list[int] = []
    blunders = 0
    mistakes = 0
    inaccuracies = 0
    severe = 0
    our_moves = 0
    first_blunder_move = None
    phase_moves: Counter[str] = Counter()
    phase_blunders: Counter[str] = Counter()
    phase_cpl: dict[str, list[int]] = defaultdict(list)
    eval_buckets = {
        "equal": {"moves": 0, "blunders": 0, "cpl": []},
        "better": {"moves": 0, "blunders": 0, "cpl": []},
        "winning": {"moves": 0, "blunders": 0, "cpl": []},
        "worse": {"moves": 0, "blunders": 0, "cpl": []},
        "lost": {"moves": 0, "blunders": 0, "cpl": []},
    }
    time_buckets = {
        "under_20": {"moves": 0, "blunders": 0},
        "over_20": {"moves": 0, "blunders": 0},
    }
    fast_open = {"moves": 0, "blunders": 0, "cpl": []}
    slow_open = {"moves": 0, "blunders": 0, "cpl": []}
    hang_yes = {"moves": 0, "cpl": []}
    hang_no = {"moves": 0, "cpl": []}
    motifs: Counter[str] = Counter()
    notable = []

    for index, step in enumerate(steps):
        if step["mover"] != color:
            continue
        our_moves += 1
        after = None
        if index + 1 < len(steps):
            after = steps[index + 1]["score_before"]
        elif board.is_checkmate():
            after = 100000 if board.turn == chess.BLACK else -100000
        elif board.is_game_over():
            after = 0
        if after is None:
            continue
        before_pov = player_pov(step["score_before"], color)
        after_pov = player_pov(after, color)
        cpl = before_pov - after_pov
        capped = max(0, min(cpl, 1500))
        components.append(capped)
        phase_moves[step["phase"]] += 1
        phase_cpl[step["phase"]].append(capped)
        if before_pov >= 90000:
            bucket = "winning"
        elif before_pov <= -90000:
            bucket = "lost"
        elif before_pov >= 400:
            bucket = "winning"
        elif before_pov <= -400:
            bucket = "lost"
        elif before_pov >= 150:
            bucket = "better"
        elif before_pov <= -150:
            bucket = "worse"
        else:
            bucket = "equal"
        eval_buckets[bucket]["moves"] += 1
        eval_buckets[bucket]["cpl"].append(capped)
        low_clock = step["clock_before"] is not None and step["clock_before"] < 20
        time_key = "under_20" if low_clock else "over_20"
        if step["clock_before"] is not None:
            time_buckets[time_key]["moves"] += 1
        spent = None
        if step["clock_before"] is not None and step["clock_after"] is not None:
            spent = step["clock_before"] + increment - step["clock_after"]
            if spent < -1 or spent > base + 30:
                spent = None
        is_blunder = cpl >= 300
        is_mistake = cpl >= 150
        is_inacc = cpl >= 80
        if is_blunder:
            blunders += 1
            phase_blunders[step["phase"]] += 1
            eval_buckets[bucket]["blunders"] += 1
            if step["clock_before"] is not None:
                time_buckets[time_key]["blunders"] += 1
            if first_blunder_move is None and before_pov > -200:
                first_blunder_move = step["fullmove"]
        if is_mistake:
            mistakes += 1
        if is_inacc:
            inaccuracies += 1
        if cpl >= 700:
            severe += 1

        scratch = chess.Board(step["fen_before"])
        material_event = move_material_loss(scratch, step["move"], color)
        material_loss = max(0, int(material_event["loss"]))
        punish_san = material_event["punish_san"]
        scratch.push(step["move"])
        if material_loss >= 2:
            hang_yes["moves"] += 1
            hang_yes["cpl"].append(capped)
        else:
            hang_no["moves"] += 1
            hang_no["cpl"].append(capped)

        if step["phase"] == "ouverture" and step["fullmove"] <= 8:
            target = fast_open if spent is not None and spent < 2 else slow_open
            target["moves"] += 1
            target["cpl"].append(capped)
            if is_blunder:
                target["blunders"] += 1

        motif = classify_motif(
            cpl=cpl,
            phase=step["phase"],
            material_loss=material_loss,
            best_san=step["best_san"],
            before_pov=before_pov,
            after_pov=after_pov,
            low_clock=low_clock,
        )
        if is_mistake:
            motifs[motif] += 1
        if cpl >= 250 and -200 <= before_pov <= 700:
            notable.append(
                {
                    "url": row["url"],
                    "date": row["date"],
                    "color": row["color"],
                    "result": row["result"],
                    "line": row["line"],
                    "eco_family": row["eco_family"],
                    "fullmove": step["fullmove"],
                    "san": step["san"],
                    "best_san": step["best_san"],
                    "pv": step["pv"],
                    "cpl": cpl,
                    "eval_before": before_pov,
                    "eval_after": after_pov,
                    "phase": step["phase"],
                    "clock_before": None if step["clock_before"] is None else round(step["clock_before"], 1),
                    "spent": None if spent is None else round(spent, 1),
                    "motif": motif,
                    "material_loss": material_loss,
                    "hang": format_punish(material_loss, punish_san),
                    "fen_before": step["fen_before"],
                    "fen_after": scratch.fen(),
                }
            )

    acpl = mean(components)
    return {
        "url": row["url"],
        "date": row["date"],
        "month": row["month"],
        "color": row["color"],
        "result": row["result"],
        "our_elo": row["our_elo"],
        "opp_elo": row["opp_elo"],
        "line": row["line"],
        "eco_family": row["eco_family"],
        "plies": row["plies"],
        "our_moves": our_moves,
        "acpl_capped": round_or_none(acpl, 1),
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "severe": severe,
        "first_blunder_move": first_blunder_move,
        "phase_moves": dict(phase_moves),
        "phase_blunders": dict(phase_blunders),
        "phase_acpl": {key: round_or_none(mean(value), 1) for key, value in phase_cpl.items()},
        "eval_buckets": {
            key: {
                "moves": value["moves"],
                "blunders": value["blunders"],
                "acpl": round_or_none(mean(value["cpl"]), 1),
            }
            for key, value in eval_buckets.items()
        },
        "time_buckets": time_buckets,
        "fast_open": {**fast_open, "cpl": round_or_none(mean(fast_open["cpl"]), 1)},
        "slow_open": {**slow_open, "cpl": round_or_none(mean(slow_open["cpl"]), 1)},
        "hang_yes": {"moves": hang_yes["moves"], "median_cpl": median(hang_yes["cpl"]), "mean_cpl": round_or_none(mean(hang_yes["cpl"]), 1)},
        "hang_no": {"moves": hang_no["moves"], "median_cpl": median(hang_no["cpl"]), "mean_cpl": round_or_none(mean(hang_no["cpl"]), 1)},
        "motifs": dict(motifs),
        "notable": notable,
    }


def classify_motif(
    cpl: int,
    phase: str,
    material_loss: int,
    best_san: str | None,
    before_pov: int,
    after_pov: int,
    low_clock: bool,
) -> str:
    if before_pov <= -90000:
        return "deja_perdu"
    if best_san and "#" in best_san and cpl >= 150:
        return "mat_manque"
    if after_pov <= -90000 < before_pov:
        return "mat_autorise"
    if material_loss >= 9:
        return "perte_dame"
    if material_loss >= 5:
        return "perte_lourde"
    if material_loss >= 3:
        return "perte_piece"
    if material_loss >= 2:
        return "perte_deux"
    if low_clock and cpl >= 150:
        return "zeitnot"
    if phase == "ouverture" and cpl >= 150:
        return "ouverture"
    if phase == "finale" and cpl >= 150:
        return "finale"
    if best_san and ("x" in best_san or "+" in best_san) and cpl >= 150:
        return "tactique"
    if cpl >= 150:
        return "positionnel"
    return "leger"


def engine_path() -> str:
    env = os.environ.get("STOCKFISH")
    if env:
        return env
    for candidate in ("/usr/games/stockfish", "/usr/bin/stockfish"):
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("Stockfish introuvable. Installez-le ou définissez STOCKFISH.")


def combine_engine(games: list[dict], depth: int, sample_meta: dict) -> dict:
    motif_counts: Counter[str] = Counter()
    phase_moves: Counter[str] = Counter()
    phase_blunders: Counter[str] = Counter()
    eval_buckets = {
        key: {"moves": 0, "blunders": 0}
        for key in ("equal", "better", "winning", "worse", "lost")
    }
    time_buckets = {"under_20": {"moves": 0, "blunders": 0}, "over_20": {"moves": 0, "blunders": 0}}
    fast_open = {"moves": 0, "blunders": 0}
    slow_open = {"moves": 0, "blunders": 0}
    hang_yes_cpl: list[float] = []
    hang_no_cpl: list[float] = []
    hang_yes_n = 0
    hang_no_n = 0
    notables = []
    by_result = {}
    for result in ("win", "loss", "draw"):
        subset = [game for game in games if game["result"] == result]
        by_result[result] = {
            "n": len(subset),
            "acpl": round_or_none(mean([game["acpl_capped"] for game in subset if game["acpl_capped"] is not None]), 1),
            "blunders_per_game": round_or_none(mean([game["blunders"] for game in subset]), 2),
            "mistakes_per_game": round_or_none(mean([game["mistakes"] for game in subset]), 2),
            "median_first_blunder": median(
                [game["first_blunder_move"] for game in subset if game["first_blunder_move"]]
            ),
        }
    for game in games:
        motif_counts.update(game["motifs"])
        phase_moves.update(game["phase_moves"])
        phase_blunders.update(game["phase_blunders"])
        for key, value in game["eval_buckets"].items():
            eval_buckets[key]["moves"] += value["moves"]
            eval_buckets[key]["blunders"] += value["blunders"]
        for key, value in game["time_buckets"].items():
            time_buckets[key]["moves"] += value["moves"]
            time_buckets[key]["blunders"] += value["blunders"]
        fast_open["moves"] += game["fast_open"]["moves"]
        fast_open["blunders"] += game["fast_open"]["blunders"]
        slow_open["moves"] += game["slow_open"]["moves"]
        slow_open["blunders"] += game["slow_open"]["blunders"]
        hang_yes_n += game["hang_yes"]["moves"]
        hang_no_n += game["hang_no"]["moves"]
        if game["hang_yes"]["mean_cpl"] is not None and game["hang_yes"]["moves"]:
            hang_yes_cpl.extend([game["hang_yes"]["mean_cpl"]] * game["hang_yes"]["moves"])
        if game["hang_no"]["mean_cpl"] is not None and game["hang_no"]["moves"]:
            hang_no_cpl.extend([game["hang_no"]["mean_cpl"]] * game["hang_no"]["moves"])
        notables.extend(game["notable"])

    notables.sort(key=lambda item: -item["cpl"])
    picked = []
    per_url: Counter[str] = Counter()
    per_motif: Counter[str] = Counter()
    for item in notables:
        if per_url[item["url"]] >= 2 or per_motif[item["motif"]] >= 6:
            continue
        per_url[item["url"]] += 1
        per_motif[item["motif"]] += 1
        item = dict(item)
        item["ascii_after"] = str(chess.Board(item["fen_after"]))
        picked.append(item)
        if len(picked) >= 24:
            break

    clean = [
        game
        for game in games
        if game["result"] == "win" and game["blunders"] == 0 and game["plies"] >= 24 and game["acpl_capped"] is not None
    ]
    clean.sort(key=lambda game: game["acpl_capped"])

    per_game = [
        {
            "url": game["url"],
            "date": game["date"],
            "color": game["color"],
            "result": game["result"],
            "line": game["line"],
            "acpl_capped": game["acpl_capped"],
            "blunders": game["blunders"],
            "mistakes": game["mistakes"],
            "severe": game["severe"],
            "first_blunder_move": game["first_blunder_move"],
            "plies": game["plies"],
        }
        for game in games
    ]
    months = Counter(game["month"] for game in games)
    colors = Counter(game["color"] for game in games)
    results = Counter(game["result"] for game in games)
    return {
        "engine": sample_meta["engine_name"],
        "depth": depth,
        "threads": sample_meta["threads"],
        "thresholds_cp": {"inaccuracy": 80, "mistake": 150, "blunder": 300, "severe": 700, "acpl_cap": 1500},
        "selection": sample_meta["selection"],
        "n_games": len(games),
        "n_our_moves": sum(game["our_moves"] for game in games),
        "by_month": dict(months),
        "by_color": dict(colors),
        "by_result_n": dict(results),
        "acpl_capped_mean": round_or_none(mean([game["acpl_capped"] for game in games if game["acpl_capped"] is not None]), 1),
        "acpl_capped_median": round_or_none(median([game["acpl_capped"] for game in games if game["acpl_capped"] is not None]), 1),
        "blunders_per_game": round_or_none(mean([game["blunders"] for game in games]), 2),
        "mistakes_per_game": round_or_none(mean([game["mistakes"] for game in games]), 2),
        "severe_per_game": round_or_none(mean([game["severe"] for game in games]), 2),
        "by_result": by_result,
        "phase_moves": dict(phase_moves),
        "phase_blunders": dict(phase_blunders),
        "eval_buckets": eval_buckets,
        "time_buckets": time_buckets,
        "opening_speed": {"fast_under_2s": fast_open, "other_opening_moves": slow_open},
        "hang_correlation": {
            "new_piece_hang_moves": hang_yes_n,
            "other_moves": hang_no_n,
            "mean_capped_cpl_when_hang": round_or_none(mean(hang_yes_cpl), 1),
            "mean_capped_cpl_otherwise": round_or_none(mean(hang_no_cpl), 1),
        },
        "motifs_mistake_or_worse": dict(motif_counts),
        "examples": picked,
        "clean_wins": [
            {
                "url": game["url"],
                "date": game["date"],
                "color": game["color"],
                "line": game["line"],
                "acpl_capped": game["acpl_capped"],
                "plies": game["plies"],
            }
            for game in clean[:5]
        ],
        "games": per_game,
    }


def slim_row(row: dict) -> dict:
    return {key: value for key, value in row.items() if key not in {"game", "color_enum"}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse le corpus d'entraînement")
    parser.add_argument("--pgn-dir", type=Path, default=ROOT / "games" / "pgn")
    parser.add_argument("--out", type=Path, default=ROOT / "analyses" / "2026-11-19-stats.json")
    parser.add_argument("--sample", type=int, default=100)
    parser.add_argument("--depth", type=int, default=12)
    parser.add_argument("--corpus-only", action="store_true")
    args = parser.parse_args()

    self_test()
    print("self-test ok", flush=True)
    started = time.perf_counter()
    games = load_games(args.pgn_dir)
    print(f"pgn lus {len(games)}", flush=True)
    skipped: Counter[str] = Counter()
    rows = []
    for index, game in enumerate(games, start=1):
        walked = walk_game(game)
        if walked is None:
            skipped["pas_zoliandru"] += 1
            continue
        if walked.get("skip"):
            skipped[walked["skip"]] += 1
            continue
        rows.append(walked)
        if index % 100 == 0:
            print(f"  corpus {index}/{len(games)}", flush=True)
    rows.sort(key=lambda row: row["when"])
    corpus = aggregate_corpus(rows)
    corpus["skipped"] = dict(skipped)
    corpus["walk_seconds"] = round(time.perf_counter() - started, 1)
    print(
        f"corpus {corpus['n']} score {corpus['results']['score']} "
        f"hangs/partie {corpus['hangs']['all']['piece_hangs_per_game']} "
        f"en {corpus['walk_seconds']}s",
        flush=True,
    )

    engine_report = None
    if not args.corpus_only:
        sample = select_sample(rows, args.sample)
        path = engine_path()
        engine = chess.engine.SimpleEngine.popen_uci(path)
        threads = 2
        engine.configure({"Threads": threads, "Hash": 256})
        engine_name = engine.id.get("name", "stockfish")
        analysed = []
        print(f"échantillon {len(sample)} profondeur {args.depth} {engine_name}", flush=True)
        try:
            for index, row in enumerate(sample, start=1):
                t0 = time.perf_counter()
                try:
                    analysed.append(analyze_with_engine(engine, row, args.depth))
                except chess.engine.EngineError:
                    engine.quit()
                    engine = chess.engine.SimpleEngine.popen_uci(path)
                    engine.configure({"Threads": threads, "Hash": 256})
                    analysed.append(analyze_with_engine(engine, row, args.depth))
                game_report = analysed[-1]
                print(
                    f"  [{index}/{len(sample)}] {row['date']} {row['result']} "
                    f"gaffes {game_report['blunders']} acpl {game_report['acpl_capped']} "
                    f"{time.perf_counter() - t0:.1f}s",
                    flush=True,
                )
        finally:
            engine.quit()
        engine_report = combine_engine(
            analysed,
            args.depth,
            {
                "engine_name": engine_name,
                "threads": threads,
                "selection": (
                    "Parties blitz classées, échecs standard, au moins 16 demi-coups. "
                    "Quotas de victoires, défaites et nulles calés sur le corpus, "
                    "répartis uniformément dans le temps. Pas de tirage aléatoire."
                ),
            },
        )

    payload = {
        "generated_at": datetime.now(BRUSSELS).isoformat(timespec="seconds"),
        "timezone": "Europe/Brussels",
        "username": USER,
        "window_note": "Corpus = PGN blitz/rapide standard présents dans games/pgn.",
        "corpus": corpus,
        "engine": engine_report,
    }
    # Les objets Game ne sont pas dans corpus ; rows non sérialisés.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"écrit {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
