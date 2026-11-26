#!/usr/bin/env python3
"""Décide s'il faut construire une nouvelle release patchée.

Entrées (variables d'environnement) :
  APP_NAME           Nom affiché dans le titre de release (ex. "Droid-ify")
  APK_PREFIX         Préfixe du fichier APK (ex. "droidify")
  UPSTREAM_KIND      "github-release" (releases/latest GitHub) ou "git-tags" (tags stables X.Y.Z)
  UPSTREAM_REPO      "owner/repo" GitHub (pour github-release)
  UPSTREAM_GIT       URL git clonable (pour git-tags)
  INPUT_UPSTREAM_TAG Tag forcé (optionnel)
  INPUT_BUMP_TYPE    auto | minor | patch | none
  INPUT_FORCE_BUILD  true | false
  GH_TOKEN           Jeton GitHub (lecture API + gh release view)

Sorties (GITHUB_OUTPUT) : should_build, upstream_tag, patch_version, build_index,
release_tag, release_title, apk_name.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

STABLE_TAG = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def latest_github_release(repo: str) -> str:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "timer-patcher",
            **({"Authorization": f"Bearer {env('GH_TOKEN')}"} if env("GH_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        rel = json.loads(resp.read().decode("utf-8"))
    if rel.get("prerelease") or rel.get("draft"):
        raise SystemExit("La dernière release amont est une pré-release/brouillon : ignorée.")
    return rel["tag_name"].strip()


def latest_stable_git_tag(url: str) -> str:
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", url],
        check=True, capture_output=True, text=True, timeout=120,
    ).stdout
    tags = []
    for line in out.splitlines():
        tag = line.split("refs/tags/", 1)[-1].strip()
        m = STABLE_TAG.match(tag)
        if m:
            tags.append((tuple(map(int, m.groups())), tag))
    if not tags:
        raise SystemExit(f"Aucun tag stable trouvé sur {url}")
    return max(tags)[1]


def main() -> None:
    with open("state.json", encoding="utf-8") as f:
        state = json.load(f)
    last_upstream = state.get("last_upstream_tag", "").strip()
    current_patch = state.get("patch_version", "0.0.0").strip()
    last_index = int(state.get("build_index", 0))

    bump_type = env("INPUT_BUMP_TYPE", "auto") or "auto"
    force_build = env("INPUT_FORCE_BUILD", "false").lower() == "true"

    target_tag = env("INPUT_UPSTREAM_TAG")
    if not target_tag:
        kind = env("UPSTREAM_KIND")
        if kind == "github-release":
            target_tag = latest_github_release(env("UPSTREAM_REPO"))
        elif kind == "git-tags":
            target_tag = latest_stable_git_tag(env("UPSTREAM_GIT"))
        else:
            raise SystemExit(f"UPSTREAM_KIND inconnu : {kind!r}")

    new_upstream = target_tag != last_upstream
    should_build = force_build or new_upstream
    print(f"Dernier tag construit : {last_upstream or '(aucun)'} (patch v{current_patch}, index {last_index})")
    print(f"Tag amont cible       : {target_tag}")
    print(f"force_build={force_build}, bump_type={bump_type}")

    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", current_patch)
    if not m:
        raise SystemExit(f"patch_version invalide dans state.json : {current_patch}")
    major, minor, patch = map(int, m.groups())
    if bump_type == "none":
        next_patch = f"{major}.{minor}.{patch}"
    elif bump_type == "minor" or (bump_type == "auto" and new_upstream):
        next_patch = f"{major}.{minor + 1}.0"
    else:
        next_patch = f"{major}.{minor}.{patch + 1}"

    # Index ajouté au versionCode amont (×100) : garantit un versionCode toujours croissant.
    build_index = 0 if new_upstream else last_index + 1
    if build_index > 99:
        raise SystemExit("build_index > 99 pour cette version amont : versionCode saturé.")

    app_name = env("APP_NAME")
    release_tag = f"{target_tag}-patch-v{next_patch}"
    release_title = f"{app_name} {target_tag} - patch v{next_patch}"
    apk_name = f"{env('APK_PREFIX')}-{target_tag}-patch-v{next_patch}.apk"

    if should_build:
        r = subprocess.run(["gh", "release", "view", release_tag], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"La release {release_tag} existe déjà : aucun build nécessaire.")
            should_build = False

    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a", encoding="utf-8") as out:
        out.write(f"should_build={'true' if should_build else 'false'}\n")
        out.write(f"upstream_tag={target_tag}\n")
        out.write(f"patch_version={next_patch}\n")
        out.write(f"build_index={build_index}\n")
        out.write(f"release_tag={release_tag}\n")
        out.write(f"release_title={release_title}\n")
        out.write(f"apk_name={apk_name}\n")
    print(f"Décision : should_build={should_build} -> {release_title} ({release_tag})")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        raise
