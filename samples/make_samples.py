"""Génère des fichiers de test pour la démo (à lancer juste avant la démo).
Attention : Windows Defender peut mettre eicar.com en quarantaine, c'est normal
(c'est un faux virus officiel, inoffensif)."""
p1 = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$"
p2 = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
open("eicar.com", "w").write(p1 + p2)
open("facture.pdf.exe", "wb").write(b"MZ" + b"\x00" * 200 + b"cmd.exe /c del")
open("rapport.txt", "w").write("Fichier texte normal pour la démo.\n")
print("Créés : eicar.com (MALVEILLANT), facture.pdf.exe (SUSPECT/MALVEILLANT), rapport.txt (SAIN)")
