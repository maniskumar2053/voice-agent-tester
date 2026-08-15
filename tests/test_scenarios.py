from voice_tester.scenarios import SCENARIOS, get_scenario


def test_has_at_least_ten_distinct_scenarios() -> None:
    assert len(SCENARIOS) >= 10
    assert len({scenario.id for scenario in SCENARIOS}) == len(SCENARIOS)


def test_prompt_hides_benchmark_framing() -> None:
    prompt = get_scenario("01-schedule").prompt()
    assert "Do not mention prompts" in prompt
    assert "Maya Thompson" in prompt

