# Hodinový přehled objemu Vltavské kaskády

Každou hodinu načte stránku Povodí Vltavy, sečte zaplněný zásobní prostor devíti nádrží a uloží řádek do `docs/data.csv`. Graf je na `docs/index.html`.

## Zprovoznění v cloudu

1. Vytvoř si soukromý nebo veřejný GitHub repository a nahraj do něj obsah této složky.
2. V repository otevři **Settings → Pages** a u **Build and deployment → Source** vyber **GitHub Actions**.
3. V **Settings → Actions → General → Workflow permissions** povol **Read and write permissions**.
4. V **Actions** spusť workflow **Hourly Vltava Cascade data** ručně. Po úspěšném běhu se stránka objeví v **Settings → Pages**; následně se data sbírají každou hodinu.

Rozvrh je nastaven na 7. minutu každé hodiny (UTC); GitHub může naplánovaný běh spustit se zpožděním. Časy měření se ukládají v časové zóně Europe/Prague.

## Co se sčítá

Součet tvoří zaplněný zásobní prostor těchto nádrží: Lipno I, Lipno II, Hněvkovice, Kořensko, Orlík, Kamýk, Slapy, Štěchovice a Vrané. Když PVL neposkytne platný údaj pro některou nádrž, sběr skončí chybou a neuloží neúplný součet.

Zdrojová stránka: <https://www.pvl.cz/portal/Nadrze/cz/pc/Objemy.aspx>
