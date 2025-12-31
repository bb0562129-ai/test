#!/usr/bin/env python3
"""
AUTHORIZED UDP traffic generator
For lab / firewall / ISP testing ONLY
"""

import socket
import time
import argparse
import signal

running = True


def stop_handler(sig, frame):
    global running
    running = False
    print("\n[!] Stopping...")


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="Target IP")
    parser.add_argument("--port", type=int, default=5201, help="Target port")
    parser.add_argument("--mbps", type=float, default=1000, help="Target Mbps")
    parser.add_argument("--size", type=int, default=1400, help="Packet size bytes")
    parser.add_argument("--duration", type=int, default=30, help="Duration seconds")
    parser.add_argument("--batch", type=int, default=32, help="Packets per loop")
    args = parser.parse_args()

    # Calculations
    bytes_per_sec = (args.mbps * 1_000_000) / 8
    bytes_per_batch = args.size * args.batch
    batches_per_sec = bytes_per_sec / bytes_per_batch
    interval = 1.0 / batches_per_sec

    # Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)

    payload = b"A" * args.size

    sent_bytes = 0
    sent_packets = 0
    start = time.monotonic()
    next_send = start

    print(f"""
================ UDP TEST =================
Target   : {args.ip}:{args.port}
Rate     : {args.mbps} Mbps
Pkt Size : {args.size} bytes
Batch    : {args.batch} packets
Duration : {args.duration} s
==========================================
""")

    try:
        while running:
            now = time.monotonic()
            if now - start >= args.duration:
                break

            if now >= next_send:
                for _ in range(args.batch):
                    sock.sendto(payload, (args.ip, args.port))
                sent_bytes += bytes_per_batch
                sent_packets += args.batch
                next_send += interval
            else:
                # Short spin instead of sleep (more accurate)
                time.sleep(0)

    finally:
        sock.close()
        elapsed = max(time.monotonic() - start, 0.001)
        mb = sent_bytes / (1024 * 1024)
        avg_mbps = (mb * 8) / elapsed

        print(f"""
============= SUMMARY =====================
Time       : {elapsed:.2f} s
Data Sent : {mb:.2f} MB
Packets   : {sent_packets}
Avg Rate  : {avg_mbps:.2f} Mbps
==========================================
""")


if __name__ == "__main__":
    main()
