#!/usr/bin/env python3
import sys
import time
import cmd
import subprocess
import socket

# Codes de style ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"

BANNER = f"""{CYAN}{BOLD}
  ____       _                           
 |  _ \\ __ _| |_ ___ _ __ ___  ___  _ __  
 | |_) / _` | __/ _ \\ '__/ __|/ _ \\| '_ \\ 
 |  __/ (_| | ||  __/ |  \\__ \\ (_) | | | |
 |_|   \\__,_|\\__\\___|_|  |___/\\___/|_| |_|
{RESET}{YELLOW}:: Personal Framework CLI :: v1.1.0{RESET}
"""

class PatersonShell(cmd.Cmd):
    prompt = f"{RED}paterson{RESET}({CYAN}framework{RESET}) > "
    intro = BANNER + f"\nTape {BOLD}help{RESET} pour les voir.\n"

    def do_ping(self, arg):
        """Tester la joignabilité d'une cible : ping <adresse_ip_ou_domaine>"""
        if not arg:
            print(f"{RED}[!] Erreur :{RESET} Spécifie une cible (ex: ping 8.8.8.8)")
            return
        
        target = arg.split()[0]
        print(f"{GREEN}[*]{RESET} Envoi de paquets ICMP vers {BOLD}{target}{RESET}...")
        
        # Adaptation du paramètre de comptage selon l'OS (Linux vs Windows)
        param = "-c" if sys.platform != "win32" else "-n"
        command = ["ping", param, "4", target]
        
        try:
            # Exécute la commande système et affiche le résultat en direct dans le terminal
            subprocess.run(command)
        except Exception as e:
            print(f"{RED}[!] Erreur d'exécution :{RESET} {e}")

    def do_portscan(self, arg):
        """Vérifier l'état d'un port TCP : portscan <ip> <port>"""
        parts = arg.split()
        if len(parts) < 2:
            print(f"{RED}[!] Erreur :{RESET} Utilisation : portscan <ip> <port> (ex: portscan 127.0.0.1 80)")
            return
        
        target = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            print(f"{RED}[!] Erreur :{RESET} Le port doit être un nombre entier valide.")
            return

        print(f"{GREEN}[*]{RESET} Scan du port {BOLD}{port}{RESET} sur {target}...")
        
        # Création d'un socket TCP IPv4
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0) # Timeout de 2 secondes max
        
        try:
            # connect_ex renvoie 0 si la connexion réussit (port ouvert)
            result = sock.connect_ex((target, port))
            if result == 0:
                print(f"{GREEN}[+][SUCCESS]{RESET} Le port {port} est {BOLD}OUVERT{RESET} sur {target}.")
            else:
                print(f"{YELLOW}[-][CLOSED]{RESET} Le port {port} est fermé ou filtré.")
        except socket.gaierror:
            print(f"{RED}[!] Erreur :{RESET} Impossible de résoudre l'adresse de l'hôte '{target}'.")
        except Exception as e:
            print(f"{RED}[!] Erreur réseau :{RESET} {e}")
        finally:
            sock.close()

    def do_info(self, arg):
        """Afficher les informations du framework"""
        print(f"{CYAN}[INFO]{RESET} Auteur : Paterson")
        print(f"{CYAN}[INFO]{RESET} Modules actifs : subprocess, socket, cmd")

    def do_exit(self, arg):
        """Quitter le shell interactif"""
        print(f"\n{YELLOW}[*]{RESET} Fermeture de la session. À bientôt !")
        return True

    do_quit = do_exit

def main():
    try:
        PatersonShell().cmdloop()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[*]{RESET} Interruption détectée. Fermeture...")

if __name__ == "__main__":
    main()