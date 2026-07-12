"""CLI for the Fleek Content Brain prototype.

Commands:
  generate-data           build the synthetic 1,000-creator roster + 90d of posts
  report                  activation %, CAC, AOV — overall and top segments
  plan-budget [--budget]  weekly reallocation plan toward best-CAC segments
  brief <CREATOR_ID>      profile the creator and print their personalised brief
  brief-real <HANDLE>     brief a REAL French creator from their scraped posts
  weekly-cycle [--limit]  end-to-end: target -> profile -> brief -> simulate -> feed back
"""

from __future__ import annotations

import argparse
import os
import random
import runpy
from datetime import date, timedelta
from pathlib import Path

from content_brain import activation, budget, evidence as evidence_mod, feedback, segmentation, store
from content_brain.brief_generator import generate_brief
from content_brain.engine_io import load_env
from content_brain.llm import get_llm
from content_brain.models import Brief, Creator, Post
from content_brain.profiler import build_profile, build_profile_from_evidence

TODAY = date(2026, 7, 1)


def cmd_generate_data(_: argparse.Namespace) -> None:
    runpy.run_path(str(Path(__file__).parent / "scripts" / "generate_roster.py"), run_name="__main__")


def cmd_report(_: argparse.Namespace) -> None:
    creators, posts = store.load_creators(), store.load_posts()
    s = activation.activation_summary(creators, posts)
    print("=== CHANNEL (last 30 days) ===")
    print(f"Roster: {s['roster']}  |  Partners posted: {s['partners_posted']} "
          f"({s['activation_pct']}% activation)  |  Posts: {s['posts']}")
    print(f"First orders: {s['first_orders']}  |  CAC: £{s['cac']}  |  AOV: £{s['aov']}")
    print(f"Lifecycle mix: {s['lifecycle_mix']}\n")
    print("=== TOP SEGMENTS BY SPEND (last 30 days) ===")
    print(f"{'segment':<45}{'creators':>9}{'active%':>9}{'orders':>8}{'CAC':>8}{'AOV':>8}")
    for st in segmentation.segment_stats(creators, posts)[:15]:
        cac = f"£{st.cac:.0f}" if st.cac else "—"
        aov = f"£{st.aov:.0f}" if st.aov else "—"
        print(f"{st.segment:<45}{st.creators:>9}{st.activation_pct:>8.0f}%{st.first_orders:>8}{cac:>8}{aov:>8}")


def cmd_plan_budget(args: argparse.Namespace) -> None:
    creators, posts = store.load_creators(), store.load_posts()
    stats = segmentation.segment_stats(creators, posts)
    lines = budget.plan_budget(stats, weekly_budget=args.budget)
    print(f"=== WEEKLY BUDGET PLAN (£{args.budget:,.0f}) ===")
    print(f"{'segment':<45}{'decision':>9}{'amount':>10}  rationale")
    for l in lines[:25]:
        print(f"{l.segment:<45}{l.decision:>9}{'£%.0f' % l.proposed_amount:>10}  {l.rationale}")


def cmd_brief(args: argparse.Namespace) -> None:
    creators, posts = store.load_creators(), store.load_posts()
    creator = next((c for c in creators if c.id == args.creator_id), None)
    if creator is None:
        raise SystemExit(f"No creator {args.creator_id}")
    if get_llm().mock:
        print("(mock mode — set ANTHROPIC_API_KEY for Claude-generated output)\n")
    history = segmentation.creator_history(creator, posts)
    seg = next((s for s in segmentation.segment_stats(creators, posts, since_days=90)
                if s.segment == creator.segment), None)
    profile = build_profile(creator, history, seg)
    store.save_profile(profile)
    print(f"=== PROFILE: {creator.handle} ({creator.segment}, {creator.lifecycle}) ===")
    print(profile.model_dump_json(indent=1))
    brief = generate_brief(creator, profile, store.load_insights())
    store.save_brief(brief)
    print(f"\n=== BRIEF {brief.brief_id} ===")
    print(brief.model_dump_json(indent=1))


def cmd_brief_real(args: argparse.Namespace) -> None:
    """Brief a real French creator from their actual scraped posts.

    This is the deck's Section 4 demo. Three creators, three lifecycles, one system:
        python run_campaign.py brief-real juliacourcelle                    # inherited, re-activation
        python run_campaign.py brief-real felixbeauregard                   # new recruit, onboarding
        python run_campaign.py brief-real lina_momo_ --lifecycle active     # active, always-on
    """
    if args.mock:
        # `env -u ANTHROPIC_API_KEY` is not enough: load_env() would put the key straight back
        # from the workspace .env. Mock has to be an explicit choice.
        os.environ.pop("ANTHROPIC_API_KEY", None)
    else:
        load_env()  # ANTHROPIC_API_KEY from the workspace .env, before the client is built

    llm = get_llm()
    if llm.mock:
        print("(mock mode — deterministic template, NOT a personalised brief)\n")

    evidence = evidence_mod.load_evidence(args.handle, lifecycle=args.lifecycle)
    c = evidence.creator
    print(f"=== EVIDENCE: @{c.handle} ===")
    print(f"segment           {c.segment}")
    print(f"lifecycle         {c.lifecycle}"
          + ("  (inferred: already carries a live Fleek code)" if evidence.has_referral_history else ""))
    print(f"posts scraped     {len(evidence.top_posts)}")
    if evidence.has_referral_history:
        print(f"referral code     {evidence.referral_code} "
              f"({evidence.referral_post_count} of {len(evidence.top_posts)} posts)")
    else:
        print(f"referral code     none yet — this is brief #1")
    if evidence.referral_evidence:
        print(f"field evidence    \"{evidence.referral_evidence[:130]}…\"")
    print(f"trend context     {len(evidence.trend_note):,} chars from the wiki (cached prompt prefix)")

    profile = build_profile_from_evidence(evidence)
    print(f"\n=== PROFILE ===")
    print(profile.model_dump_json(indent=1))

    brief = generate_brief(
        c, profile, store.load_insights(),
        campaign="FR launch — activation", evidence=evidence,
    )
    store.save_brief(brief)
    print(f"\n=== BRIEF {brief.brief_id} ===")
    print(brief.model_dump_json(indent=1))
    print(f"\nprompt cache: {llm.cache_report()}")


def _simulate_post_from_brief(creator: Creator, brief: Brief, rng: random.Random) -> Post:
    """Cheap simulator: briefed posts follow the recommended format and get a fit bonus —
    stand-in for real post tracking so the feedback loop has something to learn from."""
    view_rate = {"tiktok": 1.5, "youtube": 0.35, "instagram": 0.6}[creator.channel]
    ctr = {"tiktok": 0.0008, "youtube": 0.0025, "instagram": 0.0012}[creator.channel]
    cvr = {"tiktok": 0.05, "youtube": 0.11, "instagram": 0.07}[creator.channel]
    trust = {"nano": 3.5, "micro": 2.5, "mid": 1.4, "macro": 1.0, "mega": 0.7}[creator.tier]
    fit = 1.4  # brief personalisation bonus
    views = int(creator.followers * view_rate * rng.uniform(0.5, 1.5))
    clicks = int(views * ctr * trust * fit)
    signups = int(clicks * 0.2)
    orders = int(signups * cvr * fit) or rng.choice([0, 1])
    aov = {"tiktok": 86, "instagram": 100, "youtube": 126}[creator.channel]
    revenue = orders * aov * rng.uniform(0.8, 1.2)
    hook_type = brief.hooks[0].split(")")[0].strip("(") if brief.hooks[0].startswith("(") else "result-first"
    return Post(
        creator_id=creator.id, posted=TODAY + timedelta(days=rng.randint(1, 6)),
        format=brief.format, hook_type=hook_type, brief_id=brief.brief_id,
        views=views, clicks=clicks, signups=signups, first_orders=orders,
        revenue=round(revenue, 2),
        spend=round(creator.monthly_gifting_cost / 2 + revenue * creator.affiliate_rate, 2),
    )


def cmd_weekly_cycle(args: argparse.Namespace) -> None:
    rng = random.Random(7)
    creators, posts = store.load_creators(), store.load_posts()
    if get_llm().mock:
        print("(mock mode — set ANTHROPIC_API_KEY for Claude-generated profiles/briefs/insights)\n")

    targets = activation.next_cycle_targets(creators, limit=args.limit)
    print(f"1) TARGETING — {len(targets)} creators selected "
          f"({', '.join(f'{c.id}:{c.lifecycle}' for c in targets[:8])}…)\n")

    seg_stats = {s.segment: s for s in segmentation.segment_stats(creators, posts, since_days=90)}
    insights = store.load_insights()
    new_posts: list[Post] = []
    for c in targets:
        profile = build_profile(c, segmentation.creator_history(c, posts), seg_stats.get(c.segment))
        store.save_profile(profile)
        brief = generate_brief(c, profile, insights)
        store.save_brief(brief)
        print(f"2) BRIEFED {c.id} ({c.lifecycle:8s}) -> {brief.brief_id}: "
              f"{brief.format} | hook: {brief.hooks[0][:70]}")
        # assume ~60% of briefed creators post this cycle
        if rng.random() < 0.6:
            new_posts.append(_simulate_post_from_brief(c, brief, rng))

    print(f"\n3) SIMULATED {len(new_posts)} posts from briefed creators "
          f"({sum(p.first_orders for p in new_posts)} first orders)")
    store.append_posts(new_posts)

    all_posts = posts + new_posts
    cycle_posts = [p for p in all_posts if p.posted >= TODAY - timedelta(days=30)]
    new_insights = feedback.codify_insights(creators, cycle_posts, min_posts=3)
    store.save_insights(new_insights)
    print(f"\n4) FEEDBACK — codified {len(new_insights)} segment insights (fed into next cycle):")
    for i in new_insights[:5]:
        print(f"   {i.segment}: {i.recommended_play} [{i.confidence}]")

    s = activation.activation_summary(creators, all_posts)
    print(f"\n5) CHANNEL AFTER CYCLE — activation {s['activation_pct']}%, "
          f"{s['first_orders']} first orders (30d), CAC £{s['cac']}, AOV £{s['aov']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate-data").set_defaults(func=cmd_generate_data)
    sub.add_parser("report").set_defaults(func=cmd_report)
    p = sub.add_parser("plan-budget")
    p.add_argument("--budget", type=float, default=10_000)
    p.set_defaults(func=cmd_plan_budget)
    p = sub.add_parser("brief")
    p.add_argument("creator_id")
    p.set_defaults(func=cmd_brief)
    p = sub.add_parser("brief-real", help="brief a real French creator by handle")
    p.add_argument("handle")
    p.add_argument("--lifecycle", choices=["new", "active", "at_risk", "dormant", "core"],
                   default=None, help="override; inferred from referral history if omitted")
    p.add_argument("--mock", action="store_true",
                   help="force offline template mode, ignoring any key in .env")
    p.set_defaults(func=cmd_brief_real)
    p = sub.add_parser("weekly-cycle")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_weekly_cycle)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
