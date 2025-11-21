import argparse, concurrent.futures, time, urllib.request

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--port', type=int, default=8082)
    ap.add_argument('--path', default='/books/book1.txt')
    ap.add_argument('--concurrency', type=int, default=50)
    ap.add_argument('--requests', type=int, default=500)
    args = ap.parse_args()

    url = f'http://{args.host}:{args.port}{args.path}'
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(fetch, url) for _ in range(args.requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futs)]
    dt = time.time() - t0
    ok = sum(1 for r in results if r == 200)
    print(f"Done {len(results)} requests, {ok} OK, elapsed {dt:.3f}s")

if __name__ == "__main__":
    main()
