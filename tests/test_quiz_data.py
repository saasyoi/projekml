import pytest

from api.quiz import QUIZ_BANK, BADGE_MAP

TOPICS = list(QUIZ_BANK.keys())


@pytest.mark.parametrize("topic", TOPICS)
def test_topic_has_title(topic):
    assert isinstance(QUIZ_BANK[topic]["title"], str) and QUIZ_BANK[topic]["title"]


@pytest.mark.parametrize("topic", TOPICS)
@pytest.mark.parametrize("level", ["dasar", "lanjutan"])
def test_level_has_three_questions(topic, level):
    assert len(QUIZ_BANK[topic][level]) == 3


@pytest.mark.parametrize("topic", TOPICS)
@pytest.mark.parametrize("level", ["dasar", "lanjutan"])
def test_questions_are_well_formed(topic, level):
    for q in QUIZ_BANK[topic][level]:
        assert set(q["options"].keys()) == {"A", "B", "C", "D"}
        assert q["correct"] in q["options"]
        assert isinstance(q["explanation"], str) and q["explanation"]
        assert isinstance(q["question"], str) and q["question"]


def test_every_topic_level_has_a_badge():
    for topic in TOPICS:
        for level in ("dasar", "lanjutan"):
            assert (topic, level) in BADGE_MAP


def test_badges_are_unique():
    names = list(BADGE_MAP.values())
    assert len(names) == len(set(names))
