from sqlalchemy import select

from checkmate.checker import url
from checkmate.models import CustomRule, Reason


class CustomRuleService:
    def __init__(self, db):
        self._db = db

    def set_block_list(self, text: str) -> list[str]:
        rules, errors = self._parse_text(text)
        if not errors:
            self._set_custom_rules(rules)
        return errors

    def get_block_list(self) -> str:
        lines = [
            self._render_line(rule)
            for rule in self._db.execute(select(CustomRule).order_by(CustomRule.rule))
            .scalars()
            .all()
        ]
        return "\n".join(lines)

    @staticmethod
    def _render_line(rule: CustomRule) -> str:
        reasons = ",".join(tag.value for tag in rule.reasons)
        return f"{rule.rule} {reasons}"

    def _set_custom_rules(self, rules: list[CustomRule]) -> None:
        self._db.query(CustomRule).delete()
        CustomRule.bulk_upsert(self._db, values=rules)

    def _parse_text(self, text: str) -> tuple[list[CustomRule], list[str]]:
        rules, errors = [], []
        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                domain, reason = self._parse_line(line)
            except ValueError as e:
                errors.append(str(e))
                continue

            try:
                rules.append(url.CustomRules.value_from_domain(domain, reason))
            except ValueError as e:
                errors.append(str(e))

        return rules, errors

    @staticmethod
    def _parse_line(line: str) -> tuple[str, Reason] | None:
        match = url.BlocklistParser.LINE_PATTERN.match(line)
        if not match:
            raise ValueError(f"Cannot parse blocklist line: {line!r}")

        raw_rule, reason = match.group(1), match.group(2)
        return raw_rule, Reason.parse(reason)


def factory(_context, request):
    return CustomRuleService(request.db)
