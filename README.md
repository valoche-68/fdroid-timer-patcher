# F-Droid — patch « minuteries de mises à jour »

Dépôt **patcher** (façon Morphe) : il ne contient pas le code de F-Droid, seulement un patch appliqué automatiquement sur **chaque nouvelle version stable officielle** de [F-Droid](https://gitlab.com/fdroid/fdroidclient), puis compilé, signé et publié dans les [Releases](../../releases).

## Ce que le patch ajoute

Dans **Paramètres** de l'application :

| Réglage | Choix |
|---|---|
| **Intervalle de recherche des mises à jour** (synchro des dépôts) | heures + minutes, minimum 15 min |
| **Installation automatique** | Désactivée · Juste après chaque recherche · Minuterie séparée |
| ↳ en mode *Minuterie séparée* | intervalle (h + min, ≥ 15 min) · réseau (Wi-Fi seul / tout réseau) · seulement en charge · seulement si l'appareil est inactif |

### Spécificités F-Droid

- Basé sur la variante **full** (celle publiée sur f-droid.org : partage Nearby/Swap, extension privilégiée).
- F-Droid 2.0 sépare déjà la recherche et l'installation, mais avec des durées fixes : **4 h** pour la recherche et **24 h** pour l'installation, cette dernière seulement si l'appareil est inactif. Le patch rend ces durées réglables, ajoute le mode **« Juste après chaque recherche de mises à jour »** (même nom interne `Immediately` que sur la branche de développement de F-Droid) et rend les conditions « en charge » et « appareil inactif » activables (désactivées par défaut).
- Textes ajoutés en anglais et en français (les autres langues affichent l'anglais pour les nouveaux réglages).

> [!NOTE]
> Android planifie ces tâches de façon **approximative** (WorkManager / JobScheduler) : minimum 15 min, et l'exécution peut être retardée par le mode Doze, l'économiseur de batterie ou des conditions non remplies (réseau, charge…).

L'application est installée sous un **nom de paquet distinct** (`org.fdroid.fdroid.timer`) : elle cohabite avec la version officielle. Le nom affiché reste « F-Droid ».

> [!IMPORTANT]
> Sur Android 12+, une mise à jour n'est silencieuse que si l'app est l'**installateur d'origine** de l'app mise à jour. Les apps installées par la version officielle peuvent donc demander une confirmation une première fois ; ensuite les mises à jour sont silencieuses.

## Fonctionnement automatique (GitHub Actions)

- **Tous les jours à 10h01 (heure de Paris)** : le workflow vérifie la dernière version stable officielle (tags stables `X.Y.Z` du dépôt officiel GitLab `fdroid/fdroidclient`). Rien de nouveau → arrêt en quelques secondes.
- **Nouvelle version détectée** : clone du tag officiel → `scripts/apply_patch.sh` → tests unitaires → build release → signature (`scripts/sign_apk.sh`, certificat vérifié) → release GitHub avec l'APK + `SHA256SUMS.txt` → mise à jour de `state.json`.
- **Nommage** : `F-Droid <version officielle> - patch v<version du patch>` (ex. `F-Droid 2.0.3 - patch v0.1.0`).
- **Version du patch** : `+0.1.0` à chaque nouvelle version officielle, `+0.0.1` pour une reconstruction de la même version.
- **versionCode** = versionCode officiel × 100 + index de reconstruction → toujours croissant (mises à jour acceptées par Android/Obtainium).
- Si le patch ne s'applique plus ou qu'un test échoue, le workflow échoue (e-mail standard de GitHub Actions).

### Déclenchement manuel

**Actions → Auto-Patch & Build → Run workflow** :
- `upstream_tag` : vide = dernière stable, ou un tag précis ;
- `bump_type` : `auto` / `minor` / `patch` / `none` ;
- `force_build` : reconstruire une version déjà publiée (ex. après correction du patch).

## Secrets requis

| Secret | Description |
|---|---|
| `KEY_JKS` | keystore PKCS12 encodé en base64 (une ligne) |
| `ALIAS` | alias de la clé |
| `ANDROID_KEY_PASSWORD` | mot de passe de la clé |
| `ANDROID_STORE_PASSWORD` | mot de passe du keystore |

Empreinte SHA-256 du certificat attendu : `6a06af7388b2dfae619c129b72dde7f005a6b8794384eed716d124a952dfe15a`.

## Mettre à jour le patch

```bash
git clone --depth 1 --branch <tag> https://gitlab.com/fdroid/fdroidclient.git work
bash scripts/apply_patch.sh work      # ou résoudre les conflits à la main
# … modifier / corriger dans work/, compiler, tester …
bash scripts/regen_patch.sh work      # réécrit patches/*.patch
```
Puis committer et relancer le workflow avec `force_build`.
