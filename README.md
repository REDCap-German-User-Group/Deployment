## Projekt-spezifisches Backup-Skript


Das Python-Skript
[redcap-projects-backup.py](redcap-projects-backup.py) (ausgeführt als
cron-job) erstellt anhand einer Liste von PID's und zugehörigen Tokens
Backups. Die Konstanten zu Beginn des Skriptes müssen natürlich angepasst werden.

In ein Log-File werden die SHA1-Hashcodes aller Backups vermerkt, 
und es werden nur Backups erstellt, wenn sich etwas geändert hat. 

Das Ziel ist

- projektspezifisches Restore ermöglichen, auch Tage/Wochen später
- eine Art inkrementelles Backup, wenn man eine REDCap-Instanz mit vielen
  nicht-so-aktiven Projekten hat. 
