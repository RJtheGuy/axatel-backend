
import json

EXCLUDED_MODELS = {
    "wagtailsearch.sqliteftsindexentry",  # SQLite-only search index, rebuildable
    "wagtailcore.referenceindex",          # derived cache, rebuildable
    "core.navigationsettings",             # schema changed this session (links -> items); rebuild fresh in the admin
    "casi.casosuccessotag",                # known natural-key incompatibility (see DATABASE_MIGRATION.md); tags need re-adding manually after load
    "wagtailcore.modellogentry",           # admin audit log, references models deleted this session (SiteTheme); not real content
}

with open("data_backup.json", "r", encoding="utf-8") as f:
    data = json.load(f)

before = len(data)
filtered = [obj for obj in data if obj.get("model") not in EXCLUDED_MODELS]
after = len(filtered)

with open("data_backup_filtered.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"Removed {before - after} SQLite-only entries.")
print(f"Wrote data_backup_filtered.json ({after} objects).")
