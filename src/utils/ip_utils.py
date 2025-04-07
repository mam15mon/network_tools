import ipaddress
from typing import Union, Tuple, List
import re
from netaddr import IPRange, IPNetwork, IPAddress
from netaddr.core import AddrFormatError

class IPUtils:
    @staticmethod
    def get_binary_netmask(netmask: str) -> str:
        """获取二进制格式的子网掩码"""
        return '.'.join(format(int(x), '08b') for x in str(netmask).split('.'))

    @staticmethod
    def get_ip_class(ip: str) -> str:
        """获取IP地址类别"""
        first_octet = int(ip.split('.')[0])
        
        if first_octet == 0:  # 0.0.0.0/8
            return 'A (当前网络)'
        elif first_octet == 10:  # 10.0.0.0/8
            return 'A (私有网络)'
        elif first_octet == 127:  # 127.0.0.0/8
            return 'A (环回地址)'
        elif first_octet <= 126:
            return 'A (公网)'
        elif first_octet == 169 and int(ip.split('.')[1]) == 254:  # 169.254.0.0/16
            return 'B (本地链路)'
        elif first_octet == 172 and 16 <= int(ip.split('.')[1]) <= 31:  # 172.16.0.0/12
            return 'B (私有网络)'
        elif first_octet <= 191:
            return 'B (公网)'
        elif first_octet == 192:
            second_octet = int(ip.split('.')[1])
            third_octet = int(ip.split('.')[2])
            if second_octet == 0 and third_octet == 0:  # 192.0.0.0/24
                return 'C (IETF保留)'
            elif second_octet == 0 and third_octet == 2:  # 192.0.2.0/24
                return 'C (TEST-NET-1)'
            elif second_octet == 18:  # 192.18.0.0/15
                return 'C (IETF基准测试)'
            elif second_octet == 51 and third_octet == 100:  # 192.51.100.0/24
                return 'C (TEST-NET-2)'
            elif second_octet == 88 and third_octet == 99:  # 192.88.99.0/24
                return 'C (6to4中继)'
            elif second_octet == 168:  # 192.168.0.0/16
                return 'C (私有网络)'
            elif second_octet == 175 and third_octet == 100:  # 192.175.48.0/24
                return 'C (直接委派)'
            return 'C (公网)'
        elif first_octet <= 223:
            return 'C (公网)'
        elif first_octet <= 239:
            return 'D (组播地址)'
        else:
            return 'E (实验用)'


    @staticmethod
    def calculate_subnet_info(ip: str, prefix: int) -> dict:
        """计算子网信息"""
        try:
            network = ipaddress.IPv4Network(f'{ip}/{prefix}', strict=False)
            
            # 根据掩码长确定是否显示可用IP范围和可用主机数
            if prefix >= 31:
                ip_range = "不适用"
                usable_hosts = 0
            else:
                ip_range = f"{network.network_address + 1} - {network.broadcast_address - 1}"
                usable_hosts = network.num_addresses - 2
            
            # 获取网络地址的整数形式
            network_int = int(network.network_address)
            
            # 将32位二进制格式化为点分格式
            binary_str = format(network_int, '032b')
            formatted_binary = '.'.join(binary_str[i:i+8] for i in range(0, 32, 8))
            
            return {
                'network_address': str(network.network_address),
                'broadcast_address': str(network.broadcast_address),
                'ip_range': ip_range,
                'total_hosts': network.num_addresses,
                'usable_hosts': usable_hosts,
                'netmask': str(network.netmask),
                'hostmask': str(network.hostmask),
                'binary_netmask': IPUtils.get_binary_netmask(network.netmask),
                'ip_class': IPUtils.get_ip_class(ip),
                'prefix_length': network.prefixlen,
                # 使用点分格式的二进制
                'binary_id': formatted_binary,
                'integer_id': network_int,
                'hex_id': hex(network_int),
                'reverse_dns': f"{'.'.join(reversed(ip.split('.')))}.in-addr.arpa",
                'ipv4_mapped': f"::ffff:{format(network_int, '08x')[:4]}:{format(network_int, '08x')[4:]}",
                '6to4_prefix': f"2002:{format(network_int, '08x')[:4]}:{format(network_int, '08x')[4:]}::/48"
            }
        except Exception as e:
            raise ValueError(f"子网计算错误: {str(e)}")

    @staticmethod
    def parse_input_text(input_text):
        """通用的输入处理方法 for 路由汇总、子网计算"""
        if not input_text.strip():
            return None, "请输入IP地址列表"
        
        networks = []  # 用于精确汇总
        ip_ranges = []  # 用于非精确汇总
        
        try:
            # 处理每一行输入，支持中英文逗号、分号、换行符分隔
            for line in re.split(r'[,，;；\n]', input_text):
                line = line.strip()
                if not line or line.startswith('#'):  # 跳过空行和注释
                    continue
                    
                try:
                    if '-' in line:  # IP范围格式
                        start, end = map(str.strip, line.split('-', 1))  # 限制只分割一次
                        # 处理简写格式 (如 192.168.0.0-25 或 192.168.1.1-25)
                        if '.' not in end:
                            # 从起始IP中获取网络前缀
                            prefix = '.'.join(start.split('.')[:-1])
                            # 如果end只包含最后一个数字，添加前缀
                            end = f"{prefix}.{end}"
                        
                        # 转换为IP对象进行验证
                        start_ip = IPAddress(start)
                        end_ip = IPAddress(end)
                        
                        if start_ip > end_ip:
                            return None, f"IP范围错误: 起始IP大于结束IP\n出错的行: {line}"
                        
                        # 为非精确汇总保存IP范围
                        ip_ranges.append(IPRange(start, end))
                        
                        # 为精确汇总保存单个/32地址
                        for ip in range(int(start_ip), int(end_ip) + 1):
                            networks.append(IPNetwork(f"{IPAddress(ip)}/32"))
                        
                    else:  # CIDR或掩码格式
                        if '/' in line:  # CIDR格式
                            network = IPNetwork(line)
                            networks.append(network)
                            ip_ranges.append(IPRange(network.first, network.last))
                        else:  # 掩码格式
                            parts = line.split()
                            if len(parts) == 2:  # IP和掩码格式
                                ip, mask = parts
                                # 将点分十进制掩码转换为前缀长度
                                prefix_len = sum(bin(int(x)).count('1') for x in mask.split('.'))
                                network = IPNetwork(f"{ip}/{prefix_len}")
                                networks.append(network)
                                ip_ranges.append(IPRange(network.first, network.last))
                            else:
                                # 单个IP地址，默认使用/32
                                network = IPNetwork(f"{line}/32")
                                networks.append(network)
                                ip_ranges.append(IPRange(network.first, network.last))
                    
                except AddrFormatError as e:
                    return None, f"IP地址格式错误\n出错的行: {line}\n错误信息: {str(e)}"
                
            if not networks:
                return None, "没有有效的输入!"
                
            return {"networks": networks, "ip_ranges": ip_ranges}, None
            
        except Exception as e:
            return None, f"处理错误: {str(e)}"