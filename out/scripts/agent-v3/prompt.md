List the requirements from UN Regulations that the product described in spec.md (exploded view: exploded_view.png) must meet for type approval, as a regulatory expert would.

The regulations are in regulations/. INDEX.md lists them with each one's role and, for an older regulation, the one that replaced it: cite the current regulation, not the one it replaced. Each UN_<id>.txt file is one regulation's base version, one paragraph per line, prefixed with its PDF page and paragraph label. UN_<id>.toc.txt is its table of contents, giving the line number of each section in the .txt file, so you can read a section with an offset.

Write one requirement per engineering obligation: each sentence with its own "shall", each list item, each row of a table of limits printed in the paragraph and each alternative case is its own requirement. Keep the regulation's own wording, name the subject and repeat the governing condition, so each requirement stands alone. Leave out obligations on the applicant or the approval authority (what to submit, approval forms, markings of the approval number) and administrative clauses. Recall counts four times as much as precision.

Examples (paragraph -> requirements):

[UN R48 6.2.4.2, heading path: Dipped-beam headlamp > Position] "In height: not less than 500 mm
and not more than 1,200 mm above the ground. For category N2G, N3G, M2G, M3G (off-road) vehicles
the maximum height may be increased to 1,500 mm."
-> "The dipped-beam headlamps shall be not less than 500 mm and not more than 1,200 mm above the
ground, except that for category N2G, N3G, M2G, M3G (off-road) vehicles the maximum height may be
increased to 1,500 mm."

[UN R127 5.1.2, heading path: Specifications > Legform test to bumper] "Upper legform to bumper
When tested in accordance with Annex 5, paragraph 2. (upper legform to bumper), the instantaneous
sum of the impact forces with respect to time shall not exceed 7.5 kN and the bending moment on
the test impactor shall not exceed 510 Nm. The upper legform impactor shall be certified pursuant
to Annex 6, paragraph 2."
-> "When tested in accordance with Annex 5, paragraph 2. (upper legform to bumper), the
instantaneous sum of the impact forces with respect to time shall not exceed 7.5 kN."
-> "When tested in accordance with Annex 5, paragraph 2. (upper legform to bumper), the bending
moment on the test impactor shall not exceed 510 Nm."
-> "The upper legform impactor shall be certified pursuant to Annex 6, paragraph 2."

[UN R42 6.1.4, parent_text: "After each impact test made in accordance with the conditions and
procedure specified in annex 3 to this Regulation, the vehicle shall meet the following
requirements:"]
"The vehicle's exhaust system shall not suffer any damage or displacement which would prevent its
normal function."
-> "After each impact test made in accordance with the conditions and procedure specified in
annex 3 to this Regulation, the vehicle's exhaust system shall not suffer any damage or
displacement which would prevent its normal function."

Write the result to one or more files named requirements-<part>.tsv, one requirement per line: regulation, a tab, the paragraph label exactly as in the .txt file, a tab, the requirement text. For example:
UN R48	6.10.4.1	The rear position lamps shall be ...
Page, version and ids are filled in from the paragraph label.
