# collector/clients/iperf_client.py
import subprocess
import json
import random
import ping3
from collector.config import IPERF_SERVERS

DEFAULT_SERVERS = [
    "speedtest.uztelecom.uz",
    "iperf-ams-nl.eranium.net",
    "lon.speedtest.clouvider.net",
]

# Configuração do modo de teste
# - "tcp": Teste TCP (padrão) - mede throughput máximo
# - "udp": Teste UDP - mede jitter e perda de pacotes
# - "both": Executa ambos os testes (TCP e UDP)
TEST_MODE = "both"  # Opções: "tcp", "udp", "both"
UDP_BANDWIDTH = "250M"  # Largura de banda alvo para teste UDP (ex: "100M", "1G")


def run_iperf_tcp(server: str, duration: int = 8) -> dict:
    """
    Executa teste iPerf3 em modo TCP.
    
    Args:
        server: Servidor iPerf3
        duration: Duração do teste em segundos
    
    Returns:
        Dicionário com resultados do teste TCP
    """
    try:
        # Teste de Download (cliente -> servidor)
        result_dl = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', str(duration)],
            capture_output=True, text=True, timeout=duration + 30
        )
        data_dl = json.loads(result_dl.stdout)
        download_bps = data_dl.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)

        # Teste de Upload (servidor -> cliente) com -R (reverse)
        result_ul = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', str(duration), '-R'],
            capture_output=True, text=True, timeout=duration + 30
        )
        data_ul = json.loads(result_ul.stdout)
        upload_bps = data_ul.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)

        # Extrair ping (jitter do sender)
        ping_ms = 0.0
        streams = data_dl.get('end', {}).get('streams', [])
        if streams and len(streams) > 0:
            sender = streams[0].get('sender', {})
            ping_ms = sender.get('jitter_ms', 0)

        return {
            'protocol': 'TCP',
            'download_bps': download_bps,
            'upload_bps': upload_bps,
            'ping_ms': ping_ms,
            'data_dl': data_dl,
            'data_ul': data_ul
        }
    except subprocess.TimeoutExpired:
        print(f"iperf3 TCP timeout: {server}")
        return None
    except json.JSONDecodeError as e:
        print(f"iperf3 TCP JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"iperf3 TCP error ({server}): {e}")
        return None


def run_iperf_udp(server: str, duration: int = 8, bandwidth: str = "100M") -> dict:
    """
    Executa teste iPerf3 em modo UDP.
    
    Args:
        server: Servidor iPerf3
        duration: Duração do teste em segundos
        bandwidth: Largura de banda alvo (ex: "100M", "1G")
    
    Returns:
        Dicionário com resultados do teste UDP
    """
    try:
        # Teste de Download (cliente -> servidor) com UDP
        result_dl = subprocess.run(
            ['iperf3', '-c', server, '-u', '-J', '-t', str(duration), '-b', bandwidth],
            capture_output=True, text=True, timeout=duration + 30
        )
        data_dl = json.loads(result_dl.stdout)
        
        # Extrair métricas UDP
        download_bps = data_dl.get('end', {}).get('sum', {}).get('bits_per_second', 0)
        download_loss = data_dl.get('end', {}).get('sum', {}).get('lost_percent', 0)
        download_jitter = data_dl.get('end', {}).get('sum', {}).get('jitter_ms', 0)

        # Teste de Upload (servidor -> cliente) com UDP e -R (reverse)
        result_ul = subprocess.run(
            ['iperf3', '-c', server, '-u', '-J', '-t', str(duration), '-R', '-b', bandwidth],
            capture_output=True, text=True, timeout=duration + 30
        )
        data_ul = json.loads(result_ul.stdout)
        
        upload_bps = data_ul.get('end', {}).get('sum', {}).get('bits_per_second', 0)
        upload_loss = data_ul.get('end', {}).get('sum', {}).get('lost_percent', 0)
        upload_jitter = data_ul.get('end', {}).get('sum', {}).get('jitter_ms', 0)

        return {
            'protocol': 'UDP',
            'download_bps': download_bps,
            'upload_bps': upload_bps,
            'download_loss': download_loss,
            'upload_loss': upload_loss,
            'download_jitter': download_jitter,
            'upload_jitter': upload_jitter,
            'data_dl': data_dl,
            'data_ul': data_ul
        }
    except subprocess.TimeoutExpired:
        print(f"iperf3 UDP timeout: {server}")
        return None
    except json.JSONDecodeError as e:
        print(f"iperf3 UDP JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"iperf3 UDP error ({server}): {e}")
        return None


def run():
    """Função principal que executa os testes iPerf3."""
    servers = IPERF_SERVERS if IPERF_SERVERS and len(IPERF_SERVERS) > 0 else DEFAULT_SERVERS
    random.shuffle(servers)
    server = servers[0]

    results = {}
    ping_ms = 0.0

    # Executar testes conforme modo configurado
    if TEST_MODE in ["tcp", "both"]:
        print(f"Executando iPerf3 TCP com servidor: {server}")
        tcp_result = run_iperf_tcp(server)
        if tcp_result:
            results['tcp'] = tcp_result
            ping_ms = tcp_result.get('ping_ms', 0)

    if TEST_MODE in ["udp", "both"]:
        print(f"Executando iPerf3 UDP com servidor: {server}")
        udp_result = run_iperf_udp(server, bandwidth=UDP_BANDWIDTH)
        if udp_result:
            results['udp'] = udp_result

    # Se ambos os testes falharam, tentar ping simples
    if not results:
        try:
            ping_result = ping3.ping(server, timeout=2)
            if ping_result is not None:
                ping_ms = ping_result * 1000
        except Exception:
            pass

    # Consolidar resultados para o formato padrão
    download_bps = 0
    upload_bps = 0
    
    # Priorizar TCP se disponível, senão UDP
    if 'tcp' in results and results['tcp']:
        download_bps = results['tcp'].get('download_bps', 0)
        upload_bps = results['tcp'].get('upload_bps', 0)
    elif 'udp' in results and results['udp']:
        download_bps = results['udp'].get('download_bps', 0)
        upload_bps = results['udp'].get('upload_bps', 0)

    # Criar resultado consolidado
    result = {
        'server_id': 'iperf3',
        'sponsor': 'iPerf3',
        'server_name': server,
        'server_lat': 0,
        'server_lon': 0,
        'distance': 0,
        'ping': ping_ms,
        'download_bps': download_bps,
        'upload_bps': upload_bps,
        'test_mode': TEST_MODE,
        'detailed_results': results
    }

    # Adicionar métricas UDP se disponíveis
    if 'udp' in results and results['udp']:
        result['udp_download_loss'] = results['udp'].get('download_loss', 0)
        result['udp_upload_loss'] = results['udp'].get('upload_loss', 0)
        result['udp_download_jitter'] = results['udp'].get('download_jitter', 0)
        result['udp_upload_jitter'] = results['udp'].get('upload_jitter', 0)

    return result