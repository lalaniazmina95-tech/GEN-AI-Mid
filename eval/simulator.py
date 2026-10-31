"""Deterministic team simulator for evaluation.

Plays the team that registers a use case. It knows the hidden fact sheet and
answers ONLY the questions the chatbot asked (by field id), using the team's
own sentences. It never volunteers anything else. Missing facts are answered
honestly ("not done" for controls, "not sure" for context), which is what the
card-fabrication metric relies on.

Deterministic on purpose: the eval measures the chatbot, not a second model,
and two runs give the same team behaviour.
"""
from engine.kb.schema import FIELD_BY_ID

NA_IF_NOT_VENDOR = {"vendor_name", "third_party_due_diligence"}


class TeamSimulator:
    def __init__(self, case: dict):
        self.case = case
        self.facts = case["facts"]

    def opening(self) -> str:
        return self.case["brief"]

    def answer(self, asked: list[dict]) -> str:
        parts = []
        for i, q in enumerate(asked, 1):
            fid = q["id"]
            fact = self.facts.get(fid)
            if fact:
                parts.append(f"{i}. {fact}")
            elif fid in NA_IF_NOT_VENDOR and self.case["gold"]["flags"]["sourcing"] == "in_house":
                parts.append(f"{i}. Not applicable, we built it ourselves.")
            elif FIELD_BY_ID[fid]["kind"] == "control":
                parts.append(f"{i}. No, we have not done that yet.")
            else:
                parts.append(f"{i}. I am not sure; we have not documented that.")
        return "\n".join(parts) if parts else "That is all the information we have."
