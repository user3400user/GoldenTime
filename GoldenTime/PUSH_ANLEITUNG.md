# Push ins GitHub-Repo — Anleitung

## Variante A: Du hast schon ein lokales Git-Setup (am einfachsten)
Entpacke das ZIP, dann im entpackten Ordner:

```bash
cd GoldenTime
git init
git add .
git commit -m "Konzeptphase: STATE.md + alle Konzept-Dokumente (Stand 14.06.2026)"
git branch -M main
git remote add origin https://github.com/user3400user/GoldenTime.git
git push -u origin main
```

Falls das Repo schon Inhalte hat (z.B. eine README von GitHub), die zu einem Konflikt fuehren:
```bash
git pull origin main --allow-unrelated-histories
# evtl. Merge-Konflikt in README.md aufloesen, dann:
git push -u origin main
```

## Authentifizierung
Beim `git push` fragt GitHub nach Login. Username = dein GitHub-Name.
Als Passwort brauchst du ein **Personal Access Token** (nicht dein normales Passwort):
1. github.com -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
2. "Generate new token (classic)", Scope **repo** anhaken, generieren
3. Token kopieren, beim Push als Passwort einfuegen

Tipp: Token einmalig speichern mit `git config --global credential.helper store`
(dann fragt Git kuenftig nicht mehr).

## Variante B: GitHub CLI (falls installiert)
```bash
cd GoldenTime
gh auth login          # einmalig
git init && git add . && git commit -m "Konzeptphase Stand 14.06.2026"
git branch -M main
gh repo sync user3400user/GoldenTime --source . 2>/dev/null || git push -u origin main
```

## Danach
Im Claude-Chat den GitHub-Sync auf user3400user/GoldenTime verbinden.
STATE.md zusaetzlich im Claude-Projekt als Master-Kopie behalten.
