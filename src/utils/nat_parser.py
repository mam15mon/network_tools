import re
from typing import Optional, Dict, List

class NATParser:
    @staticmethod
    def parse_huawei_command(command: str) -> Optional[Dict]:
        """解析华为NAT Server命令"""
        pattern = r'nat server\s+(\S+)(?:\s+zone\s+\S+)?(?:\s+protocol\s+(?:tcp|udp|icmp|\d+))?\s+global\s+(\S+)(?:\s+(\S+))?\s+inside\s+(\S+)(?:\s+(\S+))?(?:\s+no-reverse|\s+acl\s+\d+)*'
        match = re.match(pattern, command)
        
        if match:
            protocol_match = re.search(r'protocol\s+(\S+)', command)
            protocol = protocol_match.group(1) if protocol_match else 'any'
            
            return {
                'name': match.group(1),
                'protocol': protocol,
                'global_ip': match.group(2),
                'global_port': match.group(3).strip() if match.group(3) else 'any',
                'inside_ip': match.group(4),
                'inside_port': match.group(5).strip() if match.group(5) else 'any',
                'command': command
            }
        return None

    @staticmethod
    def parse_h3c_command(command: str) -> Optional[Dict]:
        """解析H3C NAT Server命令"""
        pattern = r'nat server( protocol (\w+))? global (\S+)( (\d+))? inside (\S+)( (\d+))?( acl \d+)?( vrrp (\d+))? rule (\S+)( description (.+))?'
        match = re.match(pattern, command)
        
        if match:
            return {
                'protocol': match.group(2) if match.group(2) else 'any',
                'global_ip': match.group(3),
                'global_port': match.group(5) if match.group(5) else 'any',
                'inside_ip': match.group(6),
                'inside_port': match.group(8) if match.group(8) else 'any',
                'vrrp': match.group(11) if match.group(11) else '-',
                'rule': match.group(12),
                'description': match.group(14) if match.group(14) else '-',
                'command': command
            }
        return None

    @staticmethod
    def parse_config(text: str, device_type: str) -> tuple[list, list]:
        """解析NAT配置并返回结果"""
        data = []
        failed_entries = []
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('nat server'):
                try:
                    if device_type == "huawei":
                        # 保存原始命令
                        original_command = line
                        # 移除后缀用于解析
                        modified_command = re.sub(r'no-reverse.*', '', line).strip()
                        modified_command = re.sub(r'reversible.*', '', modified_command).strip()
                        parsed = NATParser.parse_huawei_command(modified_command)
                        if parsed:
                            # 使用原始命令替换修改后的命令
                            parsed['command'] = original_command
                    else:  # h3c
                        parsed = NATParser.parse_h3c_command(line)
                        
                    if parsed:
                        data.append(parsed)
                    else:
                        failed_entries.append(line)
                except Exception:
                    failed_entries.append(line)
                    
        return data, failed_entries 