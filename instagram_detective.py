#!/usr/bin/env python3

#By: HACK UNDERWAY

"""
Instagram OSINT Tool - Using Apify Instagram Scraper
"""

import os
import sys
import json
import time
import argparse
import logging
import random
import string
import threading
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

# Suprimir warnings antes de importar
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Silenciar logs solo si no estamos en modo debug
logging.getLogger().setLevel(logging.ERROR)

from dotenv import load_dotenv
from apify_client import ApifyClient
from colorama import Fore, Style, init

init(autoreset=True)

# ==============================
# COLORS & BANNER
# ==============================

class Colors:
    G1 = '\033[38;5;52m'
    G2 = '\033[38;5;88m'
    G3 = '\033[38;5;124m'
    G4 = '\033[38;5;160m'
    G5 = '\033[38;5;196m'
    RESET = '\033[0m'

BANNER = f"""
{Colors.G1}██╗ ██████╗     ██████╗ ███████╗████████╗███████╗ ██████╗████████╗██╗██╗   ██╗███████╗
{Colors.G2}██║██╔════╝     ██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██║██║   ██║██╔════╝
{Colors.G3}██║██║  ███╗    ██║  ██║█████╗     ██║   █████╗  ██║        ██║   ██║██║   ██║█████╗  
{Colors.G4}██║██║   ██║    ██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   ██║╚██╗ ██╔╝██╔══╝  
{Colors.G5}██║╚██████╔╝    ██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   ██║ ╚████╔╝ ███████╗
{Colors.G5}╚═╝ ╚═════╝     ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═══╝  ╚══════╝{Colors.RESET}
                                                                                      
{Fore.CYAN}🔍 Instagram OSINT Framework - Apify Scraper{Fore.RESET}
{Fore.RED}{Style.BRIGHT}by Hack Underway 👁{Style.RESET_ALL}
"""

def print_banner():
    print(BANNER)

# ==============================
# SPINNER / ALIVE PROGRESS
# ==============================

class Spinner:
    """Spinner animado en un hilo separado"""
    def __init__(self, message="⏳ Procesando", delay=0.1):
        self.message = message
        self.delay = delay
        self.running = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.thread = None

    def _spin(self):
        i = 0
        start_time = time.time()
        while self.running:
            elapsed = int(time.time() - start_time)
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f'\r{Fore.YELLOW}{char} {self.message}... ({elapsed}s){Fore.RESET}')
            sys.stdout.flush()
            i += 1
            time.sleep(self.delay)
        # Limpiar línea al terminar
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        # Mensaje final en verde
        sys.stdout.write(f'\r{Fore.GREEN}✅ {self.message} completado{Fore.RESET}\n')
        sys.stdout.flush()

# ==============================
# SUPPRESS OUTPUT (condicional)
# ==============================

class SuppressOutput:
    def __enter__(self):
        self.devnull = open(os.devnull, 'w')
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.devnull
        sys.stderr = self.devnull
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.devnull.close()

# ==============================
# ENV & API KEY
# ==============================

def setup_api_key():
    print(Fore.YELLOW + "🔑 Apify API Token required\n")
    token = input("👉 Enter your Apify API Token: ").strip()
    with open(".env", "w") as f:
        f.write(f"APIFY_TOKEN={token}\n")
    print(Fore.GREEN + "✅ Token saved to .env\n")
    return token

load_dotenv()
API_KEY = os.getenv("APIFY_TOKEN")

# ==============================
# INSTAGRAM SCRAPER WRAPPER
# ==============================

class InstagramScraper:
    ACTOR_ID = "apify/instagram-scraper"  # También "shu8hvrXbJbY3Eb9W"
    
    def __init__(self, api_key: str, debug: bool = False, input_key: str = "directUrls"):
        self.client = ApifyClient(api_key)
        self.debug = debug
        self.input_key = input_key
    
    def _run_actor(self, input_data: Dict[str, Any]) -> List[Dict]:
        """Ejecuta el actor y devuelve los items."""
        if self.input_key not in input_data and "urls" in input_data:
            input_data[self.input_key] = input_data.pop("urls")
        
        # Spinner (si no estamos en debug, porque en debug ya vemos logs)
        spinner = None
        if not self.debug:
            spinner = Spinner("⏳ Ejecutando scraper en Apify")
            spinner.start()
        
        try:
            if self.debug:
                print(Fore.YELLOW + "\n[DEBUG] Input enviado al actor:")
                print(json.dumps(input_data, indent=2))
                run = self.client.actor(self.ACTOR_ID).call(run_input=input_data)
            else:
                with SuppressOutput():
                    run = self.client.actor(self.ACTOR_ID).call(run_input=input_data)
        finally:
            if spinner:
                spinner.stop()
        
        if self.debug:
            print(Fore.CYAN + f"\n[DEBUG] Run ID: {run.id}")
            print(f"[DEBUG] Estado: {run.status}")
            print(f"[DEBUG] Dataset ID: {run.default_dataset_id}")
        
        dataset_id = run.default_dataset_id
        items = list(self.client.dataset(dataset_id).iterate_items())
        
        # Fallback si no hay resultados
        if not items and self.input_key == "directUrls":
            if self.debug:
                print(Fore.YELLOW + "\n[DEBUG] No se obtuvieron resultados con 'directUrls', intentando con 'urls'...")
            input_data["urls"] = input_data.pop("directUrls", [])
            with SuppressOutput():
                run2 = self.client.actor(self.ACTOR_ID).call(run_input=input_data)
            items = list(self.client.dataset(run2.default_dataset_id).iterate_items())
            if self.debug and items:
                print(Fore.GREEN + "[DEBUG] Fallback con 'urls' funcionó.")
        
        return items
    
    # Métodos de scraping (igual que antes)
    def scrape_profile_details(self, urls: List[str]) -> List[Dict]:
        input_data = {
            "resultsType": "details",
            self.input_key: urls,
            "resultsLimit": 1,
            "addProfileStatistics": True,
        }
        return self._run_actor(input_data)
    
    def scrape_posts(self, urls: List[str], limit: int = 100, date_filter: Optional[str] = None) -> List[Dict]:
        input_data = {
            "resultsType": "posts",
            self.input_key: urls,
            "resultsLimit": limit,
        }
        if date_filter:
            input_data["onlyPostsNewerThan"] = date_filter
        return self._run_actor(input_data)
    
    def scrape_reels(self, urls: List[str], limit: int = 100, date_filter: Optional[str] = None) -> List[Dict]:
        input_data = {
            "resultsType": "reels",
            self.input_key: urls,
            "resultsLimit": limit,
        }
        if date_filter:
            input_data["onlyPostsNewerThan"] = date_filter
        return self._run_actor(input_data)
    
    def scrape_comments(self, urls: List[str], limit: int = 100) -> List[Dict]:
        input_data = {
            "resultsType": "comments",
            self.input_key: urls,
            "resultsLimit": limit,
        }
        return self._run_actor(input_data)
    
    def scrape_mentions(self, urls: List[str], limit: int = 100) -> List[Dict]:
        input_data = {
            "resultsType": "mentions",
            self.input_key: urls,
            "resultsLimit": limit,
        }
        return self._run_actor(input_data)
    
    def scrape_hashtag_details(self, urls: List[str]) -> List[Dict]:
        input_data = {
            "resultsType": "details",
            self.input_key: urls,
            "resultsLimit": 1,
        }
        return self._run_actor(input_data)
    
    def scrape_place_details(self, urls: List[str]) -> List[Dict]:
        input_data = {
            "resultsType": "details",
            self.input_key: urls,
            "resultsLimit": 1,
        }
        return self._run_actor(input_data)
    
    def search(self, query: str, search_type: str, limit: int = 100) -> List[Dict]:
        input_data = {
            "search": query,
            "searchType": search_type,
            "resultsLimit": limit,
        }
        return self._run_actor(input_data)

# ==============================
# OUTPUT FORMATTING
# ==============================

def format_number(num):
    try:
        return f"{num:,}"
    except:
        return str(num)

def format_date(ts):
    if isinstance(ts, (int, float)):
        try:
            dt = datetime.fromtimestamp(ts, UTC)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return str(ts)
    return str(ts)

def print_profile_result(item: Dict):
    print(f"\n{Fore.CYAN}{'='*60}{Fore.RESET}")
    print(f"{Fore.GREEN}👤 Profile: {item.get('username', 'N/A')}{Fore.RESET}")
    print(f"   Full Name    : {item.get('fullName', 'N/A')}")
    print(f"   Verified     : {item.get('verified', False)}")
    print(f"   Private      : {item.get('private', False)}")
    print(f"   Business     : {item.get('isBusinessAccount', False)}")
    print(f"   Followers    : {format_number(item.get('followersCount', 0))}")
    print(f"   Following    : {format_number(item.get('followsCount', 0))}")
    print(f"   Posts        : {format_number(item.get('postsCount', 0))}")
    bio = item.get('biography', '')
    if bio:
        print(f"   Bio          : {bio[:200]}")
    ext_url = item.get('externalUrl', '')
    if ext_url:
        print(f"   External URL : {ext_url}")
    profile_url = item.get('url', '')
    if profile_url:
        print(f"   Profile URL  : {profile_url}")
    print(f"{Fore.CYAN}{'='*60}{Fore.RESET}")

def print_post_result(item: Dict):
    ptype = item.get('type', 'Post')
    shortcode = item.get('shortCode', '')
    caption = item.get('caption', '')[:150]
    likes = format_number(item.get('likesCount', 0))
    comments = format_number(item.get('commentsCount', 0))
    owner = item.get('ownerUsername', 'Unknown')
    timestamp = format_date(item.get('timestamp', ''))
    print(f"\n{Fore.MAGENTA}📸 {ptype} @{owner} ({shortcode}){Fore.RESET}")
    print(f"   Likes     : {likes}")
    print(f"   Comments  : {comments}")
    print(f"   Timestamp : {timestamp}")
    if caption:
        print(f"   Caption   : {caption}...")
    print(f"   URL       : {item.get('url', '')}")

def print_comment_result(item: Dict):
    owner = item.get('ownerUsername', 'Unknown')
    text = item.get('text', '')[:200]
    likes = format_number(item.get('likesCount', 0))
    timestamp = format_date(item.get('timestamp', ''))
    print(f"\n{Fore.YELLOW}💬 @{owner} ({timestamp}){Fore.RESET}")
    print(f"   {text}")
    print(f"   Likes: {likes}")

def print_hashtag_result(item: Dict):
    name = item.get('name', '')
    posts = format_number(item.get('postsCount', 0))
    print(f"\n{Fore.CYAN}#️⃣ Hashtag: #{name}{Fore.RESET}")
    print(f"   Posts: {posts}")
    related = item.get('related', [])[:5]
    if related:
        print("   Related tags:")
        for r in related:
            print(f"     #{r.get('hash', '')} ({format_number(r.get('info', 0))})")

def print_place_result(item: Dict):
    name = item.get('name', '')
    category = item.get('category', '')
    posts = format_number(item.get('media_count', 0))
    lat = item.get('lat', '')
    lng = item.get('lng', '')
    address = item.get('location_address', '')
    print(f"\n{Fore.GREEN}📍 Place: {name}{Fore.RESET}")
    print(f"   Category : {category}")
    print(f"   Posts    : {posts}")
    if lat and lng:
        print(f"   Location : {lat}, {lng}")
    if address:
        print(f"   Address  : {address}")

# ==============================
# FILE HELPERS
# ==============================

def load_urls_from_file(filepath: str) -> List[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def ensure_reports_folder():
    if not os.path.exists("reports"):
        os.makedirs("reports")

def generate_filename(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{ts}_{rand}"

def save_report(data: List[Dict], base_filename: str):
    json_path = os.path.join("reports", f"{base_filename}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    txt_path = os.path.join("reports", f"{base_filename}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("Instagram OSINT Report\n")
        f.write("="*60 + "\n")
        f.write(f"Total items: {len(data)}\n")
        f.write("="*60 + "\n\n")
        for idx, item in enumerate(data, 1):
            f.write(f"Item {idx}:\n")
            f.write(json.dumps(item, indent=2, ensure_ascii=False))
            f.write("\n\n" + "-"*40 + "\n\n")
    return json_path, txt_path

# ==============================
# CUSTOM HELP (con banner)
# ==============================

class CustomHelpFormatter(argparse.HelpFormatter):
    """Formateador que incluye el banner antes de la ayuda."""
    def __init__(self, prog):
        super().__init__(prog, max_help_position=30, width=100)

def print_help_with_banner(parser):
    """Imprime el banner y luego la ayuda."""
    print_banner()
    parser.print_help()

# ==============================
# MAIN CLI
# ==============================

def main():
    global API_KEY
    
    # Configurar parser
    parser = argparse.ArgumentParser(
        description="Instagram OSINT Tool using Apify Instagram Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Desactivamos help por defecto
        epilog="""
Examples:
  python instagram_detective.py --profile https://www.instagram.com/jeyzetaoficial/ --debug
  python instagram_detective.py --posts https://www.instagram.com/jeyzetaoficial/ --limit 50
  python instagram_detective.py --comments https://www.instagram.com/p/DZxvMgyH8yR/ --limit 20
  python instagram_detective.py --search "travel" --search-type hashtag --limit 10
  python instagram_detective.py --urls-file profiles.txt --posts --limit 100
        """
    )
    
    # Agregamos help manual
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    
    # Modos
    group = parser.add_mutually_exclusive_group(required=False)  # no required porque manejamos help
    group.add_argument("--profile", metavar="URL", help="Scrape profile details")
    group.add_argument("--posts", metavar="URL", help="Scrape posts from profile/hashtag/place")
    group.add_argument("--reels", metavar="URL", help="Scrape reels from profile/hashtag/place")
    group.add_argument("--comments", metavar="URL", help="Scrape comments from post/reel")
    group.add_argument("--mentions", metavar="URL", help="Scrape mentions from profile")
    group.add_argument("--hashtag", metavar="URL", help="Scrape hashtag details")
    group.add_argument("--place", metavar="URL", help="Scrape place details")
    group.add_argument("--search", metavar="QUERY", help="Search by query (requires --search-type)")
    group.add_argument("--urls-file", metavar="FILE", help="File with list of URLs (use with mode flags)")
    
    parser.add_argument("--search-type", choices=["user", "hashtag", "place"], help="Search type for --search")
    parser.add_argument("--limit", type=int, default=100, help="Results limit per URL (default 100)")
    parser.add_argument("--date-filter", help="Date filter (e.g., '1 day', '2024-09-05')")
    parser.add_argument("--set-api", action="store_true", help="Set Apify API token")
    parser.add_argument("--quiet", action="store_true", help="Suppress banner and non-essential output")
    parser.add_argument("--debug", action="store_true", help="Show debug logs (no suppression)")
    parser.add_argument("--input-key", default="directUrls", 
                        help="Key for URLs in input (default: directUrls; try 'urls' if not working)")
    parser.add_argument("--output-prefix", default="report", help="Prefix for output files")
    
    args = parser.parse_args()
    
    # Mostrar ayuda con banner si se pide
    if args.help:
        print_help_with_banner(parser)
        return
    
    # Si no hay acción, mostrar ayuda con banner
    if not any([args.profile, args.posts, args.reels, args.comments, args.mentions, 
                args.hashtag, args.place, args.search, args.urls_file, args.set_api]):
        print_help_with_banner(parser)
        return
    
    # Set API
    if args.set_api:
        API_KEY = setup_api_key()
        return
    
    if not API_KEY:
        API_KEY = setup_api_key()
    
    if args.search and not args.search_type:
        parser.error("--search requires --search-type")
    
    # Cargar URLs
    if args.urls_file:
        urls = load_urls_from_file(args.urls_file)
        if not urls:
            print(Fore.RED + "❌ No URLs found in file.")
            return
    else:
        if args.profile:
            urls = [args.profile]
            mode = "profile"
        elif args.posts:
            urls = [args.posts]
            mode = "posts"
        elif args.reels:
            urls = [args.reels]
            mode = "reels"
        elif args.comments:
            urls = [args.comments]
            mode = "comments"
        elif args.mentions:
            urls = [args.mentions]
            mode = "mentions"
        elif args.hashtag:
            urls = [args.hashtag]
            mode = "hashtag"
        elif args.place:
            urls = [args.place]
            mode = "place"
        elif args.search:
            urls = []
            mode = "search"
        else:
            parser.error("No action specified")
    
    if not args.quiet:
        print_banner()
    
    print(Fore.CYAN + f"\n[+] Target(s): {len(urls) if urls else 1}")
    if urls:
        for u in urls:
            print(f"    {u}")
    
    scraper = InstagramScraper(API_KEY, debug=args.debug, input_key=args.input_key)
    results = []
    
    try:
        if mode == "profile":
            results = scraper.scrape_profile_details(urls)
        elif mode == "posts":
            results = scraper.scrape_posts(urls, args.limit, args.date_filter)
        elif mode == "reels":
            results = scraper.scrape_reels(urls, args.limit, args.date_filter)
        elif mode == "comments":
            results = scraper.scrape_comments(urls, args.limit)
        elif mode == "mentions":
            results = scraper.scrape_mentions(urls, args.limit)
        elif mode == "hashtag":
            results = scraper.scrape_hashtag_details(urls)
        elif mode == "place":
            results = scraper.scrape_place_details(urls)
        elif mode == "search":
            results = scraper.search(args.search, args.search_type, args.limit)
        
        if not results:
            print(Fore.YELLOW + "\n⚠️ No results returned.")
            print(Fore.YELLOW + "   Posibles causas:")
            print(Fore.YELLOW + "   1. La clave de entrada no es la correcta (prueba --input-key urls)")
            print(Fore.YELLOW + "   2. La URL no es válida o no está accesible")
            print(Fore.YELLOW + "   3. Créditos insuficientes en Apify")
            print(Fore.YELLOW + "   Usa --debug para ver el input y el estado del run.")
            return
        
        print(Fore.GREEN + f"\n✅ Found {len(results)} items")
        
        for item in results:
            if mode == "profile":
                print_profile_result(item)
            elif mode in ("posts", "reels"):
                print_post_result(item)
            elif mode == "comments":
                print_comment_result(item)
            elif mode == "hashtag":
                print_hashtag_result(item)
            elif mode == "place":
                print_place_result(item)
            elif mode == "search":
                if 'username' in item and 'fullName' in item:
                    print_post_result(item)
                elif 'name' in item and 'postsCount' in item:
                    print_hashtag_result(item)
                elif 'name' in item and 'category' in item:
                    print_place_result(item)
                else:
                    print(json.dumps(item, indent=2))
            else:
                print(json.dumps(item, indent=2))
        
        # Guardar reportes
        ensure_reports_folder()
        base = generate_filename(args.output_prefix)
        json_path, txt_path = save_report(results, base)
        print(Fore.CYAN + f"\n📁 Reports saved:")
        print(f"   JSON: {json_path}")
        print(f"   TXT : {txt_path}")
        
    except Exception as e:
        print(Fore.RED + f"\n❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⚠️ Interrupted by user.")
        sys.exit(0)
