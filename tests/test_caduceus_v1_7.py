import hashlib
import json
import re
import unittest
from pathlib import Path

from jinja2 import Environment, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "chat-templates/qwen3.6/qwen3.6-caduceus-v1.7.jinja"
BOUNDARY_REPLAY_FIXTURE = ROOT / "tests/fixtures/caduceus_v1_7_boundary_replay.json"
V17_SHA256 = "2859a54b9e24b339d6893b30a62cd66754a41358d45a94cfa55982c8232b9228"
ADAPTATION_NOTICE = re.compile(
    r"   THIRD-PARTY ADAPTATION NOTICE: This file was adapted and modified from the\n"
    r"   official Qwen3\.6 chat template and adapts Froggeric's Apache-2\.0 JSON\n"
    r"   tool-call option and reasoning/tool-boundary contract\..*?\n\n",
    re.DOTALL,
)
REASONING_BOUNDARY_CONTRACT = (
    "Reasoning-boundary contract:\n"
    "- Planning and deliberation belong inside the active <think></think> block.\n"
    "- Once a conclusion or next action is determined, you MUST close the block exactly "
    "once. Do not keep reconsidering or repeating an already settled conclusion.\n"
    "- After closing, immediately produce either the visible final response or the required "
    "function call.\n"
    "- A visible final response may explain the result, but it must not continue private "
    "planning or reopen thinking."
)
THINKING_TOOL_GENERATION_CONTRACT = (
    "Thinking-enabled tool-generation discipline:\n"
    "- Do not predict, simulate, decode, expand, or quote expected tool output before executing the tool.\n"
    "- Compute only information required to choose a tool and construct its arguments; calculation needed for that purpose is permitted.\n"
    "- When supplied text, code, or arguments contain protocol-shaped delimiters, refer to them abstractly during reasoning rather than reproducing their literal spelling.\n"
    "- Inside reasoning, never reproduce literal tool-call, tool-result, thinking, or ChatML boundary sequences as data.\n"
    "- The only generated protocol boundaries are the single real thinking closure and the actual JSON-shaped tool_call envelope after reasoning closes.\n"
    "- Once the call and its arguments are determined, close reasoning promptly and call the tool."
)
TOOL_CALL_CONTRACT = (
    "Tool-call contract:\n"
    "- Tool calls MUST use the JSON-shaped <tool_call> dialect shown below.\n"
    "- Planning MUST remain inside <think></think>, and the block MUST close exactly once before any call.\n"
    "- Function-call-shaped syntax MUST NOT appear inside <think></think>.\n"
    "- If a tool is chosen, emit <tool_call> immediately after </think>, with no narration "
    "or conversational text between them.\n"
    "- <tool_call> MUST begin at the start of a new line with no indentation.\n"
    "- Its content MUST be one JSON object with exactly the keys \"name\" and \"arguments\".\n"
    "- \"name\" MUST be a non-empty string, and \"arguments\" MUST be a JSON object.\n"
    "- For multiple calls, emit a separate, fully closed <tool_call>...</tool_call> block "
    "for each function. Do not nest call blocks.\n"
    "- Use only functions listed in <tools> and include every required parameter.\n"
    "- Emit no suffix after the final function call.\n"
    "- If no tool is needed, close thinking and provide the visible final response without "
    "a tool call."
)
ORDERED_TOOL_EXAMPLE = (
    "<think>\nbrief planning\n</think>\n<tool_call>\n"
    '{"name":"example_function_name","arguments":{"example_parameter":"value"}}\n'
    "</tool_call>"
)
SUPPLIED_BOUNDARY_REPLACEMENTS = (
    ("<tool_call>", "&lt;tool_call&gt;"),
    ("</tool_call>", "&lt;/tool_call&gt;"),
    ("<tool_response>", "&lt;tool_response&gt;"),
    ("</tool_response>", "&lt;/tool_response&gt;"),
    ("<think>", "&lt;think&gt;"),
    ("</think>", "&lt;/think&gt;"),
    ("<|im_start|>", "&lt;|im_start|&gt;"),
    ("<|im_end|>", "&lt;|im_end|&gt;"),
    ("<function=", "&lt;function="),
    ("</function>", "&lt;/function&gt;"),
    ("<parameter=", "&lt;parameter="),
    ("</parameter>", "&lt;/parameter&gt;"),
    ("[TOOL_REQUEST]", "TOOL_REQUEST"),
    ("[END_TOOL_REQUEST]", "END_TOOL_REQUEST"),
    ("[TOOL_RESULT]", "TOOL_RESULT"),
    ("[END_TOOL_RESULT]", "END_TOOL_RESULT"),
)


def _raise_exception(message):
    raise RuntimeError(message)


def load_template(path=V17):
    environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    environment.globals["raise_exception"] = _raise_exception
    return environment.from_string(path.read_text(encoding="utf-8"))


def historical_call_payloads(rendered):
    history = "\n".join(
        re.findall(r"<\|im_start\|>assistant\n(.*?)<\|im_end\|>", rendered, flags=re.DOTALL)
    )
    payloads = re.findall(r"<tool_call>\n(.*?)\n</tool_call>", history, flags=re.DOTALL)
    return history, [json.loads(payload) for payload in payloads]


def sample_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "dummy_echo",
                "description": "Return supplied synthetic values.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "count": {"type": "number"},
                    },
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "dummy_lookup",
                "description": "Return a synthetic lookup result.",
                "parameters": {
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "required": ["key"],
                },
            },
        },
    ]


class CaduceusV17RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = load_template()

    def render(self, messages, tools=None, **kwargs):
        values = {
            "messages": messages,
            "add_generation_prompt": kwargs.pop("add_generation_prompt", True),
        }
        if tools is not None:
            values["tools"] = tools
        values.update(kwargs)
        return self.template.render(**values)

    def test_01_compiles_under_strict_undefined(self):
        self.assertIsNotNone(load_template())

    def test_01a_adaptation_notice_is_nonrendering(self):
        source = V17.read_text(encoding="utf-8")
        self.assertEqual(len(ADAPTATION_NOTICE.findall(source)), 1)
        rendered = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
        )
        environment = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
        environment.globals["raise_exception"] = _raise_exception
        without_notice = environment.from_string(
            ADAPTATION_NOTICE.sub("", source, count=1)
        ).render(
            messages=[{"role": "user", "content": "Use a dummy tool."}],
            tools=sample_tools(),
            add_generation_prompt=True,
        )
        self.assertEqual(rendered, without_notice)
        self.assertNotIn("THIRD-PARTY ADAPTATION NOTICE", rendered)
        self.assertNotIn("THIRD_PARTY_NOTICES.md", rendered)

    def test_02_coordinated_reasoning_and_tool_contract(self):
        rendered = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=True,
        )
        label = "Ordered thinking-to-tool example:\n\n"
        self.assertEqual(rendered.count(REASONING_BOUNDARY_CONTRACT), 1)
        self.assertEqual(rendered.count(THINKING_TOOL_GENERATION_CONTRACT), 1)
        self.assertEqual(rendered.count(TOOL_CALL_CONTRACT), 1)
        self.assertEqual(rendered.count(label), 1)
        example = rendered.split(label, 1)[1].split("<|im_end|>", 1)[0]
        self.assertEqual(example, ORDERED_TOOL_EXAMPLE)
        self.assertEqual(example.count("<think>"), 1)
        self.assertEqual(example.count("</think>"), 1)
        self.assertEqual(example.count("<tool_call>"), 1)
        self.assertIn("</think>\n<tool_call>", example)
        self.assertNotIn("</think>\n\n<tool_call>", example)
        self.assertIn("\n<tool_call>\n{\"name\":", "\n" + example)
        self.assertNotIn("<function=", example)
        self.assertNotIn("<parameter=", example)
        self.assertEqual(
            json.loads(example.split("<tool_call>\n", 1)[1].split("\n</tool_call>", 1)[0]),
            {"name": "example_function_name", "arguments": {"example_parameter": "value"}},
        )
        system_context = rendered.split("<|im_start|>system\n", 1)[1].split("<|im_end|>", 1)[0]
        self.assertIn(THINKING_TOOL_GENERATION_CONTRACT, system_context)
        self.assertNotIn("<function=", system_context)
        self.assertNotIn("<parameter=", system_context)
        self.assertNotIn("Ordinary narration may appear", rendered)
        self.assertNotIn("Reason about the request normally in this block", rendered)
        generation_prefill = rendered.rsplit("<|im_start|>assistant\n", 1)[1]
        self.assertEqual(generation_prefill, "<think>\n")
        self.assertEqual(generation_prefill.count("<think>"), 1)
        self.assertNotIn(THINKING_TOOL_GENERATION_CONTRACT, generation_prefill)

    def test_02a_universal_contract_applies_without_tools_when_thinking_enabled(self):
        rendered = self.render(
            [{"role": "user", "content": "Answer the synthetic question."}],
            tools=[],
            enable_thinking=True,
        )
        self.assertEqual(rendered.count(REASONING_BOUNDARY_CONTRACT), 1)
        self.assertNotIn(THINKING_TOOL_GENERATION_CONTRACT, rendered)
        self.assertNotIn(TOOL_CALL_CONTRACT, rendered)
        self.assertIn("<|im_start|>system\n" + REASONING_BOUNDARY_CONTRACT, rendered)
        generation_prefill = rendered.rsplit("<|im_start|>assistant\n", 1)[1]
        self.assertEqual(generation_prefill, "<think>\n")
        self.assertEqual(generation_prefill.count("<think>"), 1)

    def test_02b_tool_generation_discipline_is_system_only_and_permits_argument_calculation(self):
        enabled = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=True,
        )
        system_context = enabled.split("<|im_start|>system\n", 1)[1].split("<|im_end|>", 1)[0]
        self.assertEqual(system_context.count(THINKING_TOOL_GENERATION_CONTRACT), 1)
        self.assertIn(
            "calculation needed for that purpose is permitted.",
            THINKING_TOOL_GENERATION_CONTRACT,
        )
        self.assertNotIn(
            THINKING_TOOL_GENERATION_CONTRACT,
            enabled.rsplit("<|im_start|>assistant\n", 1)[1],
        )
        disabled = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=False,
        )
        self.assertNotIn(THINKING_TOOL_GENERATION_CONTRACT, disabled)

    def test_03_four_independent_thinking_control_combinations(self):
        opener = "<" + "tool_call" + ">"
        serialized = '{"key":"serialized-value"}'
        messages = [
            {"role": "user", "content": "Run the synthetic sequence."},
            {
                "role": "assistant",
                "content": "I will check the mapped value.",
                "reasoning_content": opener + "\nMapped private plan.",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "mapped"}}}
                ],
            },
            {"role": "tool", "content": "mapped-result"},
            {
                "role": "assistant",
                "content": "I will now check the serialized value.",
                "reasoning_content": "Serialized private plan.",
                "tool_calls": [
                    {"function": {"name": "dummy_lookup", "arguments": serialized}}
                ],
            },
            {"role": "tool", "content": "serialized-result"},
        ]
        combinations = (
            (True, False),
            (True, True),
            (False, False),
            (False, True),
        )
        for enable_thinking, preserve_thinking in combinations:
            with self.subTest(enable_thinking=enable_thinking, preserve_thinking=preserve_thinking):
                rendered = self.render(
                    messages,
                    sample_tools(),
                    enable_thinking=enable_thinking,
                    preserve_thinking=preserve_thinking,
                )
                self.assertIn('"name": "dummy_echo"', rendered)
                self.assertIn('"name": "dummy_lookup"', rendered)
                _, calls = historical_call_payloads(rendered)
                self.assertEqual(
                    calls,
                    [
                        {"name": "dummy_echo", "arguments": {"text": "mapped"}},
                        {"name": "dummy_lookup", "arguments": json.loads(serialized)},
                    ],
                )
                self.assertIn("<tool_response>\nmapped-result\n</tool_response>", rendered)
                self.assertIn("<tool_response>\nserialized-result\n</tool_response>", rendered)
                if enable_thinking:
                    self.assertTrue(rendered.endswith("<|im_start|>assistant\n<think>\n"))
                else:
                    self.assertTrue(rendered.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n"))
                self.assertEqual(rendered.count(TOOL_CALL_CONTRACT), 1)
                self.assertEqual(
                    rendered.count(REASONING_BOUNDARY_CONTRACT),
                    1 if enable_thinking else 0,
                )
                if preserve_thinking:
                    self.assertIn("Mapped private plan.", rendered)
                    self.assertIn("Serialized private plan.", rendered)
                    self.assertIn("&lt;tool_call&gt;", rendered)
                else:
                    self.assertNotIn("Mapped private plan.", rendered)
                    self.assertNotIn("Serialized private plan.", rendered)

    def test_04_tools_do_not_override_enable_thinking_true(self):
        rendered = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=True,
        )
        generation_prefill = rendered.rsplit("<|im_start|>assistant\n", 1)[1]
        self.assertEqual(generation_prefill, "<think>\n")
        no_tools = self.render(
            [{"role": "user", "content": "Answer normally."}],
            tools=[],
            enable_thinking=True,
        )
        self.assertEqual(
            no_tools.rsplit("<|im_start|>assistant\n", 1)[1],
            generation_prefill,
        )
        source = V17.read_text(encoding="utf-8")
        generation_source = source.split("{%- if add_generation_prompt %}", 1)[1]
        self.assertNotIn("has_tools", generation_source)
        self.assertNotIn("Reason about the request normally in this block", source)

    def test_04a_no_tools_thinking_prefill_is_unchanged(self):
        rendered = self.render(
            [{"role": "user", "content": "Answer normally."}],
            tools=[],
            enable_thinking=True,
        )
        self.assertTrue(rendered.endswith("<|im_start|>assistant\n<think>\n"))

    def test_04b_no_tools_thinking_disabled_remains_preclosed(self):
        rendered = self.render(
            [{"role": "user", "content": "Answer normally."}],
            tools=[],
            enable_thinking=False,
        )
        self.assertTrue(
            rendered.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")
        )
        self.assertNotIn(REASONING_BOUNDARY_CONTRACT, rendered)

    def test_05_tools_do_not_override_enable_thinking_false(self):
        rendered = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=False,
        )
        self.assertTrue(rendered.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n"))
        self.assertEqual(rendered.count(REASONING_BOUNDARY_CONTRACT), 0)
        self.assertEqual(rendered.count(THINKING_TOOL_GENERATION_CONTRACT), 0)
        self.assertEqual(rendered.count(TOOL_CALL_CONTRACT), 1)
        label = "Ordered thinking-to-tool example:\n\n"
        disabled_example = rendered.split(label, 1)[1].split("<|im_end|>", 1)[0]
        self.assertEqual(disabled_example, ORDERED_TOOL_EXAMPLE)

    def test_06_defaults_enable_current_thinking_and_replay_supplied_reasoning(self):
        rendered = self.render(
            [
                {"role": "user", "content": "First."},
                {"role": "assistant", "content": "Answer.", "reasoning_content": "Private completed reasoning."},
                {"role": "user", "content": "Second."},
            ],
            sample_tools(),
        )
        self.assertTrue(rendered.endswith("<|im_start|>assistant\n<think>\n"))
        self.assertIn("Private completed reasoning.", rendered)

    def test_07_single_historical_structured_call(self):
        messages = [
            {"role": "user", "content": "Call once."},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
        ]
        rendered = self.render(messages, sample_tools())
        _, calls = historical_call_payloads(rendered)
        self.assertEqual(calls, [{"name": "dummy_echo", "arguments": {"text": "one"}}])

    def test_08_parallel_historical_calls_have_separate_blocks(self):
        messages = [
            {"role": "user", "content": "Call twice."},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}},
                    {"function": {"name": "dummy_lookup", "arguments": {"key": "two"}}},
                ],
            },
        ]
        rendered = self.render(messages, sample_tools())
        history, calls = historical_call_payloads(rendered)
        self.assertEqual(
            calls,
            [
                {"name": "dummy_echo", "arguments": {"text": "one"}},
                {"name": "dummy_lookup", "arguments": {"key": "two"}},
            ],
        )
        self.assertEqual(history.count("<tool_call>"), 2)
        self.assertIn("</tool_call>\n\n<tool_call>\n{\"name\":\"dummy_lookup\"", history)

    def test_09_single_and_consecutive_tool_results(self):
        messages = [
            {"role": "user", "content": "Synthetic sequence."},
            {"role": "tool", "content": "first"},
            {"role": "tool", "content": "second"},
        ]
        rendered = self.render(messages, sample_tools())
        self.assertIn("<tool_response>\nfirst\n</tool_response>\n<tool_response>\nsecond", rendered)
        self.assertEqual(rendered.count("<|im_start|>user"), 2)  # user query plus grouped tool results

    def test_10_argument_value_types_and_empty_mapping(self):
        arguments = {
            "string_value": "text",
            "number_value": 7.5,
            "boolean_value": True,
            "list_value": [1, "two"],
            "object_value": {"quoted": "{value}"},
            "empty_value": "",
        }
        messages = [
            {"role": "user", "content": "Types."},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": arguments}},
                    {"function": {"name": "dummy_lookup", "arguments": {}}},
                ],
            },
        ]
        rendered = self.render(messages, sample_tools())
        _, calls = historical_call_payloads(rendered)
        self.assertEqual(calls[0], {"name": "dummy_echo", "arguments": arguments})
        self.assertEqual(calls[1], {"name": "dummy_lookup", "arguments": {}})

    def test_11_system_and_developer_roles_are_merged_or_rendered(self):
        messages = [
            {"role": "system", "content": "System one."},
            {"role": "developer", "content": "Developer two."},
            {"role": "user", "content": "Question."},
            {"role": "developer", "content": "Later reminder."},
        ]
        rendered = self.render(messages)
        self.assertIn("System one.\nDeveloper two.", rendered)
        self.assertIn("<|im_start|>system\nLater reminder.<|im_end|>", rendered)

    def test_12_preserve_thinking_false_drops_active_multistep_reasoning(self):
        messages = [
            {"role": "user", "content": "First."},
            {
                "role": "assistant",
                "content": "Checking now.",
                "reasoning_content": "Active multi-step reasoning.",
                "tool_calls": [{"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}],
            },
            {"role": "tool", "content": "result"},
        ]
        rendered = self.render(messages, sample_tools(), preserve_thinking=False)
        self.assertNotIn("Active multi-step reasoning.", rendered)
        self.assertIn("Checking now.", rendered)

    def test_13_preserve_thinking_true_mandatorily_sanitizes_reasoning(self):
        opener = "<" + "tool_call" + ">"
        messages = [
            {"role": "user", "content": "First."},
            {"role": "assistant", "content": "Answer.", "reasoning_content": opener + "\nOld reasoning."},
            {"role": "user", "content": "Second."},
        ]
        rendered = self.render(messages, preserve_thinking=True)
        self.assertIn("<think>\n&lt;tool_call&gt;\nOld reasoning.\n</think>", rendered)
        history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        self.assertNotIn(opener, history)

    def test_14_removed_coupled_and_optional_sanitizer_controls_are_absent(self):
        source = V17.read_text(encoding="utf-8")
        forbidden = (
            "caduceus" + "_" + "profile",
            "tool" + "_" + "reliability",
            "reasoning" + "_" + "experimental",
            "sanitize" + "_" + "preserved" + "_" + "thinking",
            "retry" + "_" + "count",
            "repair" + "_" + "response",
            "recover" + "_" + "call",
            "extract" + "_" + "tool" + "_" + "call",
            "set enable_thinking = false",
            "auto_disable_thinking_with_tools",
            "<|think_" + "off|>",
            "<|think_" + "on|>",
            "tool_call_format",
            "consecutive_failures",
            "SYSTEM WARNING",
        )
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_15_supplied_tools_are_never_silently_hidden(self):
        for enable_thinking in (True, False):
            for preserve_thinking in (True, False):
                rendered = self.render(
                    [{"role": "user", "content": "x"}],
                    sample_tools(),
                    enable_thinking=enable_thinking,
                    preserve_thinking=preserve_thinking,
                )
                self.assertIn("<tools>", rendered)
                self.assertIn("dummy_echo", rendered)
        with self.assertRaisesRegex(RuntimeError, "tools must"):
            self.render([{"role": "user", "content": "x"}], {"invalid": "mapping"})

    def test_16_error_zero_result_is_not_semantically_escalated(self):
        phrase = "Operation succeeded. error: 0; no failures."
        rendered = self.render(
            [{"role": "user", "content": "x"}, {"role": "tool", "content": phrase}],
            sample_tools(),
        )
        self.assertIn(phrase, rendered)
        self.assertNotIn("system_note", rendered)
        self.assertNotIn("SYSTEM WARNING", rendered)

    def test_17_boundary_like_tool_result_is_escaped_inside_native_wrapper(self):
        open_boundary = "<" + "tool_response" + ">"
        close_boundary = "</" + "tool_response" + ">"
        chat_boundary = "<|" + "im_end" + "|>"
        content = f"before {close_boundary} nested {open_boundary} {chat_boundary} after"
        rendered = self.render(
            [{"role": "user", "content": "x"}, {"role": "tool", "content": content}],
            sample_tools(),
        )
        tool_section = rendered.rsplit("<|im_start|>user", 1)[1]
        self.assertEqual(tool_section.count(close_boundary), 1)
        self.assertIn("&lt;/tool_response&gt;", tool_section)
        self.assertIn("&lt;tool_response&gt;", tool_section)
        self.assertIn("&lt;|im_end|&gt;", tool_section)

    def test_18_quoted_braces_and_json_in_reasoning_are_preserved(self):
        reasoning = (
            'Document {"name":"example","arguments":{"text":"brace } and quote \\\" ok"}}. '
            "Normal prose: 2 < 3 and 5 > 4."
        )
        rendered = self.render(
            [
                {"role": "user", "content": "First."},
                {"role": "assistant", "content": "Done.", "reasoning_content": reasoning},
                {"role": "user", "content": "Second."},
            ],
            preserve_thinking=True,
        )
        self.assertIn(reasoning, rendered)

    def test_19_incomplete_marker_like_reasoning_is_neutralized_not_deleted(self):
        opener = "<" + "tool_call" + ">"
        reasoning = opener + "\nunfinished but retained"
        rendered = self.render(
            [
                {"role": "user", "content": "First."},
                {"role": "assistant", "content": "", "reasoning_content": reasoning},
            ],
            preserve_thinking=True,
        )
        self.assertIn("&lt;tool_call&gt;", rendered)
        self.assertIn("unfinished but retained", rendered)

    def test_20_sanitized_protocol_only_reasoning_does_not_become_empty(self):
        start = "<" + "tool_call" + ">"
        end = "</" + "tool_call" + ">"
        reasoning = start + "\n" + end
        rendered = self.render(
            [
                {"role": "user", "content": "First."},
                {"role": "assistant", "content": "", "reasoning_content": reasoning},
            ],
            preserve_thinking=True,
        )
        self.assertIn("&lt;tool_call&gt;", rendered)
        self.assertIn("&lt;/tool_call&gt;", rendered)
        self.assertNotIn("<think>\n\n</think>", rendered)

    def test_21_argument_and_result_truncation_boundaries(self):
        def history(value, result):
            return [
                {"role": "user", "content": "Truncate."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "dummy_echo", "arguments": {"text": value}}}
                    ],
                },
                {"role": "tool", "content": result},
            ]

        exact = self.render(
            history("12345", "abcde"),
            sample_tools(),
            max_tool_arg_chars=5,
            max_tool_response_chars=5,
        )
        self.assertNotIn("[TRUNCATED:", exact)
        _, exact_calls = historical_call_payloads(exact)
        self.assertEqual(exact_calls[0]["arguments"]["text"], "12345")
        over = self.render(
            history("123456", "abcdef"),
            sample_tools(),
            max_tool_arg_chars=5,
            max_tool_response_chars=5,
        )
        _, over_calls = historical_call_payloads(over)
        self.assertEqual(
            over_calls[0]["arguments"]["text"],
            "12345\n[TRUNCATED: original length 6 chars]",
        )
        self.assertIn("abcde\n[TRUNCATED: original length 6 chars]", over)

    def test_22_final_template_matches_expected_hash(self):
        self.assertEqual(hashlib.sha256(V17.read_bytes()).hexdigest(), V17_SHA256)

    def test_23_openai_serialized_string_argument_container_replays_without_iteration(self):
        serialized_arguments = "{\"command\":\"printf 'CADUCEUS_V17_TOOL_OK\\\\n'\"}"
        messages = [
            {"role": "user", "content": "Run the synthetic terminal check."},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "terminal", "arguments": serialized_arguments}}
                ],
            },
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "terminal",
                    "description": "Run one synthetic command.",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"],
                    },
                },
            }
        ]
        rendered = self.render(messages, tools)
        history, calls = historical_call_payloads(rendered)
        self.assertEqual(calls, [{"name": "terminal", "arguments": json.loads(serialized_arguments)}])
        self.assertEqual(history.count("<tool_call>"), 1)
        self.assertNotIn("<function=", history)
        self.assertNotIn("<parameter=", history)

    def test_23a_serialized_argument_limit_fails_closed_but_exact_limit_is_preserved(self):
        serialized = '{"command":"abc"}'
        messages = [
            {"role": "user", "content": "Run."},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "terminal", "arguments": serialized}}
            ]},
        ]
        exact = self.render(messages, sample_tools(), max_tool_arg_chars=len(serialized))
        _, calls = historical_call_payloads(exact)
        self.assertEqual(calls, [{"name": "terminal", "arguments": json.loads(serialized)}])
        with self.assertRaisesRegex(RuntimeError, "cannot be safely truncated without JSON parsing"):
            self.render(messages, sample_tools(), max_tool_arg_chars=len(serialized) - 1)

    def test_23b_mapping_strings_truncate_as_json_but_structured_values_are_not_sliced(self):
        arguments = {
            "text": "abcdef",
            "nested": {"full": "abcdef"},
            "items": [1, "abcdef", None],
        }
        messages = [
            {"role": "user", "content": "Run."},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "terminal", "arguments": arguments}}
            ]},
        ]
        rendered = self.render(messages, sample_tools(), max_tool_arg_chars=3)
        _, calls = historical_call_payloads(rendered)
        self.assertEqual(
            calls[0]["arguments"]["text"],
            "abc\n[TRUNCATED: original length 6 chars]",
        )
        self.assertEqual(calls[0]["arguments"]["nested"], {"full": "abcdef"})
        self.assertEqual(calls[0]["arguments"]["items"], [1, "abcdef", None])

    def test_23c_mapping_boundary_values_remain_inside_one_json_call_wrapper(self):
        close_call = "</" + "tool_call" + ">"
        chat_end = "<|" + "im_end" + "|>"
        messages = [
            {"role": "user", "content": "Run."},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "terminal", "arguments": {"text": f"before {close_call} {chat_end} after"}}}
            ]},
        ]
        rendered = self.render(messages, sample_tools())
        history, calls = historical_call_payloads(rendered)
        self.assertEqual(history.count("<tool_call>"), 1)
        self.assertEqual(history.count(close_call), 1)
        self.assertIn("\\u003c/tool_call\\u003e", history)
        self.assertIn("\\u003c|im_end|\\u003e", history)
        self.assertEqual(calls[0]["arguments"]["text"], f"before {close_call} {chat_end} after")

    def test_24_final_template_contains_no_generic_compatibility_marker_dialect(self):
        source = V17.read_text(encoding="utf-8")
        request_marker = "[" + "TOOL_REQUEST" + "]"
        result_marker = "[" + "TOOL_RESULT" + "]"
        self.assertNotIn(request_marker, source)
        self.assertNotIn(result_marker, source)

    def test_25_unexpected_message_role_fails_rendering(self):
        with self.assertRaisesRegex(RuntimeError, "Unexpected message role"):
            self.render([{"role": "observer", "content": "unsafe"}])

    def test_26_json_escaped_historical_function_identifier_replays(self):
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "dummy > echo", "arguments": {"value": "x"}}}],
            },
        ]
        _, calls = historical_call_payloads(self.render(messages, sample_tools()))
        self.assertEqual(calls[0]["name"], "dummy > echo")

    def test_27_json_escaped_historical_argument_key_replays(self):
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "dummy_echo", "arguments": {'bad "name" <>': "x"}}}],
            },
        ]
        _, calls = historical_call_payloads(self.render(messages, sample_tools()))
        self.assertEqual(calls[0]["arguments"], {'bad "name" <>': "x"})

    def test_28_non_string_historical_identifiers_fail_rendering(self):
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": 7, "arguments": {"value": "x"}}}],
            },
        ]
        with self.assertRaisesRegex(RuntimeError, "function name must be a non-empty string"):
            self.render(messages, sample_tools())

    def test_29_identifier_validator_accepts_json_escapable_names_and_rejects_empty(self):
        valid_names = ("bad<name", "bad>name", "bad/name", "bad=name", "bad\rname", "bad\nname", "bad\tname")
        for name in valid_names:
            with self.subTest(name=repr(name)):
                messages = [
                    {"role": "user", "content": "x"},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"function": {"name": name, "arguments": {"value": "x"}}}],
                    },
                ]
                _, calls = historical_call_payloads(self.render(messages, sample_tools()))
                self.assertEqual(calls[0]["name"], name)
        empty = [
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "", "arguments": {}}}]},
        ]
        with self.assertRaisesRegex(RuntimeError, "missing a function name"):
            self.render(empty, sample_tools())

    def test_30_identifier_validator_source_contains_no_for_loop(self):
        source = V17.read_text(encoding="utf-8")
        macro = source.split("macro require_json_identifier", 1)[1].split("endmacro", 1)[0]
        self.assertNotIn("{% for", macro.replace("{%-", "{%"))
        self.assertNotIn("for character in value", macro)
        self.assertIn("non-empty string", macro)
        self.assertNotIn("native-tag boundary", macro)

    def test_31_serialized_historical_arguments_neutralize_native_and_chatml_boundaries(self):
        close_function = "</" + "function" + ">"
        close_call = "</" + "tool_call" + ">"
        chat_end = "<|" + "im_end" + "|>"
        serialized = json.dumps({"command": f"before {close_function} {close_call} {chat_end} after"})
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "terminal", "arguments": serialized}}],
            },
        ]
        rendered = self.render(messages, sample_tools())
        history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        _, calls = historical_call_payloads(rendered)
        self.assertEqual(calls, [{"name": "terminal", "arguments": json.loads(serialized)}])
        self.assertIn("\\u003c/function\\u003e", history)
        self.assertIn("\\u003c/tool_call\\u003e", history)
        self.assertIn("\\u003c|im_end|\\u003e", history)
        self.assertEqual(history.count(close_function), 0)
        self.assertEqual(history.count(close_call), 1)

    def test_32_messages_string_is_rejected_before_message_loops(self):
        with self.assertRaisesRegex(RuntimeError, "messages must be a non-string iterable"):
            self.template.render(messages="not-a-message-sequence", add_generation_prompt=True)

    def test_33_empty_or_non_mapping_historical_arguments_fail_and_missing_arguments_defaults_empty_object(self):
        for arguments in ("", None, 7, ["not", "a", "mapping"]):
            with self.subTest(arguments=arguments):
                messages = [
                    {"role": "user", "content": "x"},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"function": {"name": "terminal", "arguments": arguments}}],
                    },
                ]
                with self.assertRaisesRegex(RuntimeError, "mapping or a non-empty serialized JSON string"):
                    self.render(messages, sample_tools())
        absent = [
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "terminal"}}]},
        ]
        _, calls = historical_call_payloads(self.render(absent, sample_tools()))
        self.assertEqual(calls, [{"name": "terminal", "arguments": {}}])

    def test_34_ordinary_narration_before_structured_call_is_preserved_and_call_is_terminal(self):
        narration = "I will check the synthetic value now."
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": narration,
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
        ]
        rendered = self.render(messages, sample_tools())
        history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        self.assertTrue(history.startswith(narration + "\n\n"))
        self.assertTrue(history.endswith("}\n</tool_call>"))

    def test_35_tools_and_history_are_independent_of_both_thinking_controls(self):
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "Narration.",
                "reasoning_content": "Private reasoning.",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
            {"role": "tool", "content": "result"},
        ]
        protocol_fragments = (
            '"name": "dummy_echo"',
            '{"name":"dummy_echo","arguments":{"text":"one"}}',
            "<tool_response>\nresult\n</tool_response>",
        )
        for enable_thinking in (True, False):
            for preserve_thinking in (True, False):
                rendered = self.render(
                    messages,
                    sample_tools(),
                    enable_thinking=enable_thinking,
                    preserve_thinking=preserve_thinking,
                )
                for fragment in protocol_fragments:
                    self.assertIn(fragment, rendered)

    def test_36_preserve_true_with_absent_reasoning_does_not_fabricate_or_fail(self):
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "Narration only.",
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
            {"role": "tool", "content": "result"},
        ]
        rendered = self.render(messages, sample_tools(), preserve_thinking=True)
        history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        self.assertTrue(history.startswith("Narration only."))
        self.assertNotIn("<think>", history)
        self.assertIn('{"name":"dummy_echo","arguments":{"text":"one"}}', history)
        self.assertIn("<tool_response>\nresult\n</tool_response>", rendered)

    def test_37_single_tool_history_replays_supplied_reasoning_only_after_sanitization(self):
        opener = "<" + "tool_call" + ">"
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "First narration.",
                "reasoning_content": "SINGLE_ACTIVE_LABEL\n" + opener,
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
            {"role": "tool", "content": "first-result"},
        ]
        rendered = self.render(messages, sample_tools(), preserve_thinking=True)
        self.assertIn("SINGLE_ACTIVE_LABEL", rendered)
        self.assertIn("&lt;tool_call&gt;", rendered)
        self.assertIn('{"name":"dummy_echo","arguments":{"text":"one"}}', rendered)
        self.assertIn("<tool_response>\nfirst-result\n</tool_response>", rendered)

    def test_38_sequential_tool_history_sanitizes_each_supplied_reasoning_field(self):
        first_marker = "<" + "function=dummy_echo" + ">"
        second_marker = "<" + "parameter=key" + ">"
        messages = [
            {"role": "user", "content": "x"},
            {
                "role": "assistant",
                "content": "First narration.",
                "reasoning_content": "FIRST_ACTIVE_LABEL\n" + first_marker,
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
            {"role": "tool", "content": "first-result"},
            {
                "role": "assistant",
                "content": "Second narration.",
                "reasoning_content": "SECOND_ACTIVE_LABEL\n" + second_marker,
                "tool_calls": [
                    {"function": {"name": "dummy_lookup", "arguments": '{"key":"two"}'}}
                ],
            },
            {"role": "tool", "content": "second-result"},
        ]
        rendered = self.render(messages, sample_tools(), preserve_thinking=True)
        self.assertIn("FIRST_ACTIVE_LABEL", rendered)
        self.assertIn("SECOND_ACTIVE_LABEL", rendered)
        self.assertIn("&lt;function=dummy_echo>", rendered)
        self.assertIn("&lt;parameter=key>", rendered)
        self.assertEqual(rendered.count('{"name":"dummy_echo"'), 1)
        self.assertEqual(rendered.count('{"name":"dummy_lookup"'), 1)
        self.assertIn("<tool_response>\nfirst-result\n</tool_response>", rendered)
        self.assertIn("<tool_response>\nsecond-result\n</tool_response>", rendered)

    def test_39_preserved_reasoning_neutralizes_native_result_and_thinking_boundaries(self):
        result_open = "<" + "tool_response" + ">"
        result_close = "</" + "tool_response" + ">"
        think_open = "<" + "think" + ">"
        think_close = "</" + "think" + ">"
        cases = (
            (f"inline {result_open} synthetic {result_close} prose", "&lt;tool_response&gt;"),
            (f"before\n{result_open}\nsynthetic\n{result_close}\nafter", "&lt;/tool_response&gt;"),
            (f"inline {think_open} synthetic {think_close} prose", "&lt;think&gt;"),
            (f"before\n{think_open}\nsynthetic\n{think_close}\nafter", "&lt;/think&gt;"),
        )
        for reasoning, expected_entity in cases:
            with self.subTest(reasoning=reasoning):
                rendered = self.render(
                    [
                        {"role": "user", "content": "First."},
                        {"role": "assistant", "content": "Done.", "reasoning_content": reasoning},
                    ],
                    preserve_thinking=True,
                    add_generation_prompt=False,
                )
                history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
                body = history.split("<think>\n", 1)[1].split("\n</think>", 1)[0]
                self.assertTrue(body.strip())
                self.assertIn(expected_entity, body)
                for boundary in (result_open, result_close, think_open, think_close):
                    self.assertNotIn(boundary, body)

    def test_40_combined_shape_has_only_legitimate_history_wrappers(self):
        result_open = "<" + "tool_response" + ">"
        result_close = "</" + "tool_response" + ">"
        think_open = "<" + "think" + ">"
        think_close = "</" + "think" + ">"
        chat_start = "<|" + "im_start" + "|>"
        chat_end = "<|" + "im_end" + "|>"
        reasoning = (
            f"Observed {result_open} synthetic {result_close} and "
            f"{chat_start}assistant {chat_end} while discussing {think_open}reasoning{think_close}."
        )
        messages = [
            {"role": "user", "content": "Run the synthetic sequence."},
            {
                "role": "assistant",
                "content": "I will use the structured call.",
                "reasoning_content": reasoning,
                "tool_calls": [
                    {"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}
                ],
            },
            {"role": "tool", "content": "real-result"},
        ]
        rendered = self.render(
            messages,
            sample_tools(),
            preserve_thinking=True,
            add_generation_prompt=False,
        )
        history = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        body = history.split("<think>\n", 1)[1].split("\n</think>", 1)[0]
        self.assertTrue(body.strip())
        for boundary in (result_open, result_close, think_open, think_close, chat_start, chat_end):
            self.assertNotIn(boundary, body)
        for entity in (
            "&lt;tool_response&gt;",
            "&lt;/tool_response&gt;",
            "&lt;think&gt;",
            "&lt;/think&gt;",
            "&lt;|im_start|&gt;",
            "&lt;|im_end|&gt;",
        ):
            self.assertIn(entity, body)
        self.assertEqual(history.count(think_open), 1)
        self.assertEqual(history.count(think_close), 1)
        self.assertEqual(rendered.count(result_open), 1)
        self.assertEqual(rendered.count(result_close), 1)
        self.assertIn("<tool_response>\nreal-result\n</tool_response>", rendered)

    def test_41_supplied_content_sanitizer_uses_exact_non_parsing_split_join_replacements(self):
        source = V17.read_text(encoding="utf-8")
        macro = source.split("macro sanitize_supplied_content", 1)[1].split("endmacro", 1)[0]
        for marker, entity in SUPPLIED_BOUNDARY_REPLACEMENTS[:12]:
            self.assertIn(f"value.split('{marker}')", macro)
            self.assertIn(f"join('{entity}')", macro)
        for legacy_name, replacement in (
            ("legacy_request_start", "TOOL_REQUEST"),
            ("legacy_request_end", "END_TOOL_REQUEST"),
            ("legacy_result_start", "TOOL_RESULT"),
            ("legacy_result_end", "END_TOOL_RESULT"),
        ):
            self.assertIn(f"value.split({legacy_name})", macro)
            self.assertIn(f"join('{replacement}')", macro)
        self.assertNotIn("fromjson", macro)
        self.assertNotIn("from_json", macro)
        self.assertNotIn("{% for", macro.replace("{%-", "{%"))

    def test_42_observed_boundary_replay_fixture_is_neutralized_in_all_supplied_message_content(self):
        fixture = json.loads(BOUNDARY_REPLAY_FIXTURE.read_text(encoding="utf-8"))
        self.assertIn("<|im_end|> <|im_start|>assistant", fixture["assistant_visible_content"])
        ordinary = fixture["ordinary_text"]
        messages = [
            {"role": "system", "content": fixture["leading_system_content"] + " " + ordinary},
            {"role": "developer", "content": fixture["leading_developer_content"] + " " + ordinary},
            {"role": "user", "content": fixture["user_content"] + " " + ordinary},
            {"role": "developer", "content": fixture["later_developer_content"] + " " + ordinary},
            {
                "role": "assistant",
                "content": fixture["assistant_visible_content"] + " " + ordinary,
                "reasoning_content": fixture["assistant_reasoning_content"] + " " + ordinary,
            },
            {"role": "tool", "content": fixture["tool_result_content"] + " " + ordinary},
        ]
        rendered = self.render(
            messages,
            tools=[],
            enable_thinking=False,
            preserve_thinking=True,
            add_generation_prompt=False,
        )
        leading_system = rendered.split("<|im_start|>system\n", 1)[1].split("<|im_end|>", 1)[0]
        user = rendered.split("<|im_start|>user\n", 1)[1].split("<|im_end|>", 1)[0]
        later_developer = rendered.rsplit("<|im_start|>system\n", 1)[1].split("<|im_end|>", 1)[0]
        assistant = rendered.split("<|im_start|>assistant\n", 1)[1].split("<|im_end|>", 1)[0]
        reasoning = assistant.split("<think>\n", 1)[1].split("\n</think>\n\n", 1)[0]
        visible = assistant.split("\n</think>\n\n", 1)[1]
        tool = rendered.rsplit("<|im_start|>user", 1)[1].split("\n<tool_response>\n", 1)[1].split("\n</tool_response>", 1)[0]
        sections = {
            "leading system/developer": leading_system,
            "user": user,
            "later developer": later_developer,
            "assistant visible": visible,
            "assistant reasoning": reasoning,
            "tool result": tool,
        }
        for label, section in sections.items():
            with self.subTest(section=label):
                self.assertIn(ordinary, section)
                for marker, entity in SUPPLIED_BOUNDARY_REPLACEMENTS:
                    self.assertNotIn(marker, section)
                    self.assertIn(entity, section)

    def test_43_caduceus_owned_wrappers_and_example_remain_functional(self):
        rendered = self.render(
            [{"role": "user", "content": "Use a dummy tool."}],
            sample_tools(),
            enable_thinking=True,
            add_generation_prompt=False,
        )
        label = "Ordered thinking-to-tool example:\n\n"
        example = rendered.split(label, 1)[1].split("<|im_end|>", 1)[0]
        self.assertEqual(example, ORDERED_TOOL_EXAMPLE)
        self.assertNotIn("&lt;tool_call&gt;", example)
        self.assertNotIn("&lt;think&gt;", example)
        self.assertIn("<tools>", rendered)
        self.assertIn("</tools>", rendered)
        historical = self.render(
            [
                {"role": "user", "content": "Replay one call."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "dummy_echo", "arguments": {"text": "one"}}}],
                },
            ],
            sample_tools(),
            add_generation_prompt=False,
        )
        history, calls = historical_call_payloads(historical)
        self.assertIn("<tool_call>\n", history)
        self.assertIn("\n</tool_call>", history)
        self.assertEqual(calls, [{"name": "dummy_echo", "arguments": {"text": "one"}}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
