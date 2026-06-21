from scripts.postgres_scenario_catalog import SCENARIOS


def test_scenario_catalog_has_10_scenarios(scenario_catalog):
    assert len(scenario_catalog) == 10


def test_each_scenario_has_2_to_5_questions(scenario_catalog):
    for scenario in scenario_catalog:
        assert 2 <= len(scenario.questions) <= 5, scenario.scenario_id


def test_all_canonical_questions_return_rows(seeded_postgres_env, scenario_catalog):
    results = []
    for scenario in scenario_catalog:
        for question in scenario.questions:
            result = seeded_postgres_env.execute_query(question.canonical_sql, limit=50)
            results.append((scenario.scenario_id, question.question_id, result.row_count))
            assert result.success, (scenario.scenario_id, question.question_id, result.error_message)
            assert result.row_count >= question.min_expected_rows, (
                scenario.scenario_id,
                question.question_id,
                result.row_count,
            )

    for scenario_id, question_id, row_count in results:
        print(f"{scenario_id} | {question_id} | rows={row_count}")
