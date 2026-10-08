"""Deterministic long-document generator for the Bonsai eval (F4 tasks + context ladder).
A synthetic ops log of filler paragraphs with N fact sentences ("needles") spread through it."""
import random

SERVICES = ["Nimbus", "Quartz", "Heron", "Basalt", "Juniper", "Talon", "Cobalt", "Willow",
            "Ember", "Fjord", "Lumen", "Sable", "Tundra", "Vesper", "Zephyr", "Marlin"]
VERBS = ["reviewed", "patched", "restarted", "rebalanced", "audited", "migrated", "tuned", "inspected"]
THINGS = ["the cache tier", "the ingest queue", "the TLS certificates", "the disk quotas",
          "the alert thresholds", "the replica set", "the cron schedule", "the log rotation",
          "the firewall rules", "the backup catalog", "the DNS records", "the GPU drivers"]
OUTCOMES = ["no regressions were observed", "latency stayed within budget", "two warnings were filed for follow-up",
            "the change was rolled forward", "error rates were unchanged", "the on-call engineer signed off",
            "metrics looked nominal afterwards", "a ticket was opened to track cleanup"]

# (fact sentence, question, accepted answers) — names/values never appear in filler.
FACTS = [
    ("The maintenance window for cluster Orion-7 is Thursday at 03:40.", "When is the maintenance window for cluster Orion-7? Give day and time.", ["03:40"]),
    ("The emergency contact for the Pelican datacenter is Ingrid Solberg.", "Who is the emergency contact for the Pelican datacenter?", ["solberg"]),
    ("The archive bucket kestrel-cold-17 retains objects for 412 days.", "How many days does the archive bucket kestrel-cold-17 retain objects?", ["412"]),
    ("Build runner Saffron-3 has exactly 96 GB of RAM.", "How much RAM does build runner Saffron-3 have?", ["96"]),
    ("The rollback code word for the Meridian release is BLUE-ANCHOR.", "What is the rollback code word for the Meridian release?", ["blue-anchor", "blue anchor"]),
    ("The Graywater VPN uses UDP port 51944.", "Which UDP port does the Graywater VPN use?", ["51944"]),
    ("The quarterly disaster-recovery drill is owned by Tomas Okafor.", "Who owns the quarterly disaster-recovery drill?", ["okafor"]),
    ("The license for the Halcyon analytics suite expires on 2027-03-19.", "When does the Halcyon analytics suite license expire?", ["2027-03-19", "march 19, 2027", "19 march 2027"]),
    ("The Copperline database was last vacuumed by an operator named Ruth Achebe.", "Which operator last vacuumed the Copperline database?", ["achebe"]),
    ("The Ashgrove load balancer drains connections for 37 seconds before shutdown.", "For how many seconds does the Ashgrove load balancer drain connections before shutdown?", ["37"]),
]

def paragraph(rng):
    s = []
    for _ in range(rng.randint(4, 7)):
        s.append(f"On day {rng.randint(1, 365)} the {rng.choice(SERVICES)} team {rng.choice(VERBS)} "
                 f"{rng.choice(THINGS)} and {rng.choice(OUTCOMES)}.")
    return " ".join(s)

def make_doc(target_tokens, n_facts=10, seed=7):
    """~4.1 chars/token (measured with Bonsai's tokenizer) for this text. Facts spread at 5%..95% of the document."""
    rng = random.Random(seed + target_tokens)
    target_chars = int(target_tokens * 4.1)
    paras, total = [], 0
    while total < target_chars:
        p = paragraph(rng); paras.append(p); total += len(p) + 2
    facts = FACTS[:n_facts]
    for i, (sent, _, _) in enumerate(facts):
        pos = int(len(paras) * (0.05 + 0.9 * i / max(1, n_facts - 1)))
        paras[pos] = paras[pos] + " " + sent
    doc = "\n\n".join(f"### Log entry {i + 1}\n{p}" for i, p in enumerate(paras))
    return doc, [(q, a) for _, q, a in facts]

def score(answers, qa):
    """answers: list/dict of strings in question order. Returns number correct."""
    if isinstance(answers, dict):
        answers = [answers.get(str(i + 1), answers.get(i + 1, "")) for i in range(len(qa))]
    ok = 0
    for (q, acc), a in zip(qa, list(answers) + [""] * len(qa)):
        a = str(a).lower()
        ok += any(x in a for x in acc)
    return ok
