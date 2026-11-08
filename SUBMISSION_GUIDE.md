# CCP NIS Fall 2026 — Submission and Group-Sharing Guide

## Final deliverables

1. **Main report:** `report/CCP_NIS_Fall_2026_Report.pdf`
2. **Editable report:** `report/CCP_NIS_Fall_2026_Report.docx`
3. **Source repository:** https://github.com/Global-Tech-hub/ccp-nis-fall-2026-vrfc
4. **Group package:** one complete ZIP containing the report, editable source document, code, tests, data, actual results, charts, independent reviews, and instructions.

## LMS submission steps

1. Open the final PDF and verify the course, registration number, names, and deadline.
2. Upload the **PDF as the main report** in the LMS assignment area.
3. Paste the **GitHub repository URL** in the code-link field or LMS comment:
   `https://github.com/Global-Tech-hub/ccp-nis-fall-2026-vrfc`
4. The repository is **private**. Invite the instructor through GitHub **Settings → Collaborators** before expecting them to open the link. Invite group members who need repository access as well.
5. If the LMS permits a supplementary attachment, also upload the complete ZIP. The assignment's required code channel is GitHub; the ZIP is an additional convenience, not a replacement for the repository.
6. Submit before **8 November 2026**, then recheck that the submitted PDF and repository URL open correctly from the intended instructor account.

## Group roster check

The current cover lists **Muhammad Imaad Tahir (CR-23014)** only. If this is a group submission, add every member's name and registration number to the DOCX cover and README, export the updated PDF, and ensure the roster contains no more than four members. Do this before the final LMS upload.

## Share with group members

- Share the **one complete ZIP** through WhatsApp, Google Drive, or the group's normal file channel.
- Each member should extract it, review `README.md`, and run:

```bash
python3 -m unittest discover -s tests -v
```

- Keep the directory structure unchanged; the attacks load language data from `data/` and the report loads figures from `results/`.
- Group members without GitHub collaborator access can still review everything from the ZIP.

## Package map

```text
src/                 Comment-free cipher, attacks, experiments, and report tools
tests/               Eight automated tests
data/                Training/evaluation corpora and source attribution
results/             Raw CSV results, summaries, benchmarks, charts, verification log
report/              Final PDF, editable DOCX, and report source
reviews/             Independent GLM, Claude, and GPT reviews plus consolidated summary
README.md            Setup, commands, results, and repository link
SUBMISSION_GUIDE.md  This checklist
PLAN.md              Requirement-to-deliverable plan
GITHUB_UPLOAD.md     Published repository and access instructions
```

## Final pre-submission checklist

- [ ] Correct group roster, maximum four members
- [ ] PDF opens and all 16 pages are readable
- [ ] Eight tests pass on a member's machine
- [ ] GitHub URL is correct and instructor has private-repository access
- [ ] Report and repository describe the same version of the code
- [ ] One complete ZIP is shared with the group
- [ ] LMS submission is completed before the deadline
