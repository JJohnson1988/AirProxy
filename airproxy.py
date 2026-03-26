#!/opt/bin/python3
import socket as sck
import threading
import select
import time
import sys
import signal
import subprocess
import errno

# --- SYSTEM CONFIGURATION ---
PRINTR_ADDR = '10.1.0.30' # Change this to your printer's LAN IP address!
PRINTR_PORT = 631
LISTEN_PORT = 631
MAX_THREADS = 20 # Prevent Out-Of-Memory (OOM) panics from port scanners

def log(message, priority="notice"):
    """
    Ultra-safe Asuswrt-Merlin logging. Uses the native router logger via
    subprocess to bypass Bash shell creation, preventing RAM exhaustion.
    Use your specific router's own logging function for easy debugging!
    """
    try:
        subprocess.run(
            ['logger', '-t', 'AirProxy', '-p', f'user.{priority}', str(message)],
            check=False
        )
    except Exception:
        pass # Never allow a logging failure to crash the proxy

def handle_exit(signum, frame):
    """Graceful termination trap."""
    sig_name = signal.Signals(signum).name
    log(f"SHUTDOWN: Caught {sig_name} ({signum}). Evacuating...", "warn")
    sys.exit(0)

# Register traps for termination and interrupts
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

def bridge_connection(client_sock, client_addr):
    # Strip IPv4-mapped IPv6 prefix if present (e.g., ::ffff:192.168.1.50)
    client_ip = client_addr[0].replace('::ffff:', '')
    start_time = time.time()
    bytes_total = 0
    active_jobs = threading.active_count() - 1

    log(f"ACCEPT: Handshake from {client_ip} | Active Jobs: {active_jobs}")

    printer_sock = None
    try:
        # Force IPv4 outbound, as the printer itself does not use IPv6; if you need IPv6 you can change this
        printer_sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)

        # TCP Keep-Alives prevent strict VPN/VLAN firewalls from dropping idle rendering jobs
        client_sock.setsockopt(sck.SOL_SOCKET, sck.SO_KEEPALIVE, 1)
        printer_sock.setsockopt(sck.SOL_SOCKET, sck.SO_KEEPALIVE, 1)

        # 15s timeout allows the router's DNS to resolve the .local mDNS broadcast
        printer_sock.settimeout(15)
        printer_sock.connect((PRINTR_ADDR, PRINTR_PORT))
    except sck.timeout:
        log(f"TIMEOUT: {PRINTR_ADDR} unreachable from {client_ip}", "err")
        client_sock.close()
        if printer_sock: printer_sock.close()
        return
    except OSError as e:
        log(f"ROUTE_ERR: Network path to printer failed: {e}", "err")
        client_sock.close()
        if printer_sock: printer_sock.close()
        return

    sockets = [client_sock, printer_sock]
    try:
        while True:
            # 60s select timeout for latency tolerance on remote VPN connections
            readable, _, _ = select.select(sockets, [], [], 60)
            if not readable:
                log(f"IDLE: Dropping stale connection with {client_ip}", "warn")
                break

            for s in readable:
                try:
                    # 64KB buffer strictly minimizes fragmentation across VPN tunnels
                    data = s.recv(65536)
                    if not data:
                        break # Clean socket closure by peer

                    if s is client_sock:
                        printer_sock.sendall(data)
                        bytes_total += len(data)
                    else:
                        client_sock.sendall(data)

                except ConnectionResetError:
                    log(f"RESET: Peer disconnected abruptly ({client_ip})", "warn")
                    break
                except BrokenPipeError:
                    log(f"BROKEN_PIPE: Client {client_ip} vanished mid-stream", "warn")
                    break
                except OSError as e:
                    log(f"SOCKET_ERR: Data flow interrupted: {e}", "err")
                    break
            else:
                continue
            break

    except Exception as e:
        # Ultimate fallback for bizarre payload or stream errors
        log(f"FATAL_STREAM: Unhandled exception processing {client_ip}: {e}", "crit")
    finally:
        kb = round(bytes_total / 1024, 2)
        duration = round(time.time() - start_time, 2)

        # Only log meaningful data transfers to keep the syslog clean of Apple's 0.5KB status pings; increase value if less verbosity desired
        if kb > 1.0:
            log(f"SUCCESS: Job finished for {client_ip} | {kb}KB | {duration}s")

        # Nuclear-proof socket teardown
        try:
            client_sock.close()
        except Exception: pass
        try:
            if printer_sock: printer_sock.close()
        except Exception: pass

def main():
    log("SYSTEM: Booting *Titanium-Grade* Dual-Stack Proxy...")

    server_sock = None
    try:
        # Bind to IPv6 '::' with V6ONLY=0 natively catches BOTH IPv4 and IPv6 traffic; you can change this if you desire IPv6-only
        server_sock = sck.socket(sck.AF_INET6, sck.SOCK_STREAM)
        server_sock.setsockopt(sck.IPPROTO_IPV6, sck.IPV6_V6ONLY, 0)
    except (AttributeError, OSError):
        # Fallback if the router's Entware Python build has IPv6 stripped out
        log("SYSTEM: IPv6 stack unavailable, forcing IPv4.", "warn")
        server_sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)

    server_sock.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)

    try:
        # Bind to all interfaces (LAN, Guest VLANs, VPN tunnels)
        server_sock.bind(('', LISTEN_PORT))
        server_sock.listen(25)
        log(f"SYSTEM: Online and listening across all interfaces on Port {LISTEN_PORT}")
    except OSError as e:
        if e.errno == 98:
            log(f"FATAL: Port {LISTEN_PORT} is hijacked. Check router GUI Print Server.", "crit")
        else:
            log(f"FATAL: Bind failure - {e}", "crit")
        sys.exit(1)

    while True:
        try:
            client_sock, addr = server_sock.accept()

            # RAM/OOM Protection Shield against port scanners and runaway processes
            if threading.active_count() > MAX_THREADS:
                log(f"OVERLOAD: Rejecting {addr[0]}, max concurrent threads reached.", "warn")
                client_sock.close()
                continue

            # Daemon threads die instantly if the main process is killed
            t = threading.Thread(target=bridge_connection, args=(client_sock, addr), daemon=True)
            t.start()

        except OSError as e:
            # Shield against File Descriptor exhaustion (EMFILE/ENFILE)
            if e.errno in (errno.EMFILE, errno.ENFILE):
                log("SYSTEM: File descriptors exhausted! Sleeping 1s to recover...", "err")
                time.sleep(1)
            else:
                log(f"ACCEPT_ERR: OS rejected connection: {e}", "err")
        except Exception as e:
            log(f"CORE_ERR: Main loop exception: {e}", "crit")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("SYSTEM: Manual keyboard interrupt. Exiting.", "notice")
    except Exception as e:
        # The absolute last line of defense logging
        try:
            subprocess.run(['logger', '-t', 'AirProxy', '-p', 'user.crit', f"GLOBAL_CRASH: {str(e)}"])
        except Exception: pass
