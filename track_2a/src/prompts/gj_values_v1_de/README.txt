# SPDX-License-Identifier: Apache-2.0
Template gj_values_v1_de, SHA-256 54abf49ab788b2779b7bd00d8ebfb99abb3daf0fbe076e274fec30851dca81f6.
Model: Apertus-v1.5-8B, bf16. No text generation.
One prompt = the prefix (system.txt in the chat frame, then the document as block lines:
prefix_format.txt) + one suffix (one question). The read-out is the hidden state at the last
token of the suffix. Small heads are fitted on this state.
q0_document_kind.txt: one time for each document. Single label.
q1_affair_type.txt: one time for each document. Single label. Options A to I are the values of
the list AffairTypeEnum of eCH-0295. Options J and K are a project choice.
q2_block_values.txt: one time for each block. The places {block}, {page} and {first_words} get
the block id, the page and the first 12 words of the block. MULTI-LABEL: one binary head for
each of the 7 value kinds reads the same state. The letter is not the read-out.
template.json: the full record with the source of each option.
Code: src/m11_prompts_values.py (questions), src/m10_prompts.py (prefix).
