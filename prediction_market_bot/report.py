"""Plain-text report formatting for quote tables and detected edges."""


def _fmt(value, digits=4):
    return f"{value:.{digits}f}" if value is not None else "--"


def format_quote_table(quotes: list) -> str:
    header = f"{'source':<12}{'yes_bid':>9}{'yes_ask':>9}{'no_bid':>9}{'no_ask':>9}{'yes_mid':>9}  question"
    lines = [header, "-" * len(header)]
    for q in quotes:
        book_flag = "" if q.has_order_book else " (AMM, no book)"
        lines.append(
            f"{q.source:<12}{_fmt(q.yes_bid):>9}{_fmt(q.yes_ask):>9}{_fmt(q.no_bid):>9}"
            f"{_fmt(q.no_ask):>9}{_fmt(q.yes_mid):>9}  {q.question}{book_flag}"
        )
    return "\n".join(lines)


def format_cross_platform_edges(edges: list) -> str:
    if not edges:
        return "  (none above threshold)"
    lines = []
    for e in edges:
        lines.append(
            f"  sell {e.sell_source} Yes @ {e.sell_price:.4f}  vs  "
            f"buy {e.buy_source} Yes @ {e.buy_price:.4f}   edge = {e.edge:+.4f}"
        )
    return "\n".join(lines)


def format_complementary_edges(edges: list) -> str:
    if not edges:
        return "  (none above threshold)"
    lines = []
    for e in edges:
        action = "BUY Yes+No" if e.side == "buy" else "SELL Yes+No"
        lines.append(
            f"  {e.source}: {action}  (yes={e.yes_price:.4f} + no={e.no_price:.4f} "
            f"= {e.cost:.4f})   edge = {e.edge:+.4f}"
        )
    return "\n".join(lines)


def format_pricing_errors(errors: dict) -> str:
    if not errors:
        return "  (no data)"
    return "\n".join(f"  {source:<12} {error:+.4f} vs consensus" for source, error in sorted(errors.items()))
