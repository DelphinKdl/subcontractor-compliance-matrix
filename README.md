# Subcontractor Document and Insurance Compliance Matrix

A Streamlit prototype that tracks subcontractor insurance and safety
certification expirations and flags anything expiring soon or already
lapsed, before it becomes a liability on the jobsite. I don't have
construction field experience, so I built a small, working version of
this compliance-tracking problem myself to understand how it actually
works.

## Problem

General contractors carry financial and legal liability if a
subcontractor's General Liability insurance, Workers' Compensation, or
safety certification lapses while that subcontractor is still working on
site. With dozens of subcontractor firms on a project, each with multiple
documents on different renewal cycles, tracking expiration dates by hand
is a real administrative bottleneck for site engineers.

## My Role

I designed and built this end to end: the data model, the seed data, the
status logic, and the Streamlit interface. This is a solo prototype, not
a team project.

## The Data

All data is synthetic: 50 mock subcontractor profiles across common
construction trades, each with 2 to 3 documents (General Liability
Insurance, Workers' Compensation, and sometimes a Safety Certification).
Expiration dates are spread across compliant, expiring soon, and expired
so the demo shows real variety right away instead of a wall of green.
The data set generates the same way every time, so it's easy to retest.
No real subcontractors, projects, or people are represented anywhere in
this app.

## Tools and Techniques

- Python and SQLite for the data layer
- Streamlit for the interface
- Status computed live from each document's expiration date vs. the
  current date, never stored, so the matrix is always accurate to today
- Streamlit's `AppTest` framework for automated end-to-end verification

## The Process

1. Defined what a subcontractor and a document record needed to look
   like, and built the data generator first, before any interface, so
   there was real data to build against from the start.
2. Wrote the status logic as its own isolated piece and hand-checked the
   exact boundary cases before touching the interface.
3. Built the matrix view, then the summary stats, then the subcontractor
   detail view and alert draft feature, in that order.
4. Wrote automated tests covering the full flow: load the app, filter to
   red and yellow, select a subcontractor, generate a draft alert.

## Key Insights

- The riskiest part of this kind of tool is the status boundary logic,
  not the UI. A document that expires today has to count as already
  expired, not "expiring soon," because a subcontractor can't rely on
  coverage that lapsed at the start of the day while still working
  through it. Getting that one boundary wrong would undermine the whole
  premise of the tool.
- Computing status live from the expiration date, instead of storing a
  status value, avoids an entire class of bugs where the displayed status
  goes stale.

## Business Impact

This is a prototype built to demonstrate a pattern, not a deployed tool
with measured outcomes. I have not put a dollar figure on the value of
this because I have no real usage data to back one up. What I can say
directly: this mirrors the automated compliance-audit and
validation-gate logic I've used professionally, applied here to
subcontractor insurance and certification tracking, a problem that is
currently handled manually on most jobsites.

## Challenges and Learning

- I don't have construction field experience, so I kept the scope
  narrow and asked what a site engineer actually needs to see at a
  glance (who's non-compliant, why, and what to do about it) rather than
  trying to model every real-world edge case in subcontractor
  compliance.
- Getting the red/yellow/green boundary logic exactly right took more
  care than expected. It's a small function, but it's the part of the
  tool that actually has to be correct.
- Questions I'd want to ask a field engineer to take this further: how
  insurance certificates actually get collected and verified today, what
  other documents or credentials matter beyond the three tracked here,
  and whether something like this would need to stand alone or fit into
  an existing project management tool.

This project reflects skills directly aligned with the compliance
tracking, data validation, and audit-gate work I've done professionally,
applied to a construction-specific problem.

## Running it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 seed_db.py
streamlit run app.py
```

