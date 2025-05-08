import re
from typing import Optional, Dict, List

class NATParser:
    @staticmethod
    def parse_huawei_command(command: str) -> Optional[Dict]:
        """解析华为NAT Server命令"""
        # 预处理命令，处理带引号的标识符
        processed_command = command
        quoted_names = re.findall(r'"([^"]+)"', command)

        # 临时替换带引号的标识符，以便正则表达式处理
        for i, quoted_name in enumerate(quoted_names):
            placeholder = f"QUOTED_NAME_{i}"
            processed_command = processed_command.replace(f'"{quoted_name}"', placeholder)

        # 尝试多种模式匹配
        result = None

        # 模式1: 两个标识符格式 - nat server id1 id2 protocol ...
        pattern1 = r'nat server\s+(\S+)\s+(\S+)(?:\s+zone\s+\S+)?\s+protocol\s+(\S+)\s+global\s+(\S+)(?:\s+(\S+))?\s+inside\s+(\S+)(?:\s+(\S+))?(?:\s+no-reverse|\s+acl\s+\d+|\s+reversible)*'
        match = re.match(pattern1, processed_command)
        if match:
            id1 = match.group(1)
            id2 = match.group(2)
            protocol = match.group(3)
            global_ip = match.group(4)
            global_port = match.group(5).strip() if match.group(5) else 'any'
            inside_ip = match.group(6)
            inside_port = match.group(7).strip() if match.group(7) else 'any'

            # 还原带引号的标识符
            for i, quoted_name in enumerate(quoted_names):
                placeholder = f"QUOTED_NAME_{i}"
                if id1 == placeholder:
                    id1 = quoted_name

            # 将第一个标识符作为名称
            name = id1

            result = {
                'name': name,
                'protocol': protocol,
                'global_ip': global_ip,
                'global_port': global_port,
                'inside_ip': inside_ip,
                'inside_port': inside_port,
                'command': command
            }

        # 模式2: 单个标识符 + protocol 格式 - nat server id protocol ...
        if not result:
            pattern2 = r'nat server\s+(\S+)(?:\s+zone\s+\S+)?\s+protocol\s+(\S+)\s+global\s+(\S+)(?:\s+(\S+))?\s+inside\s+(\S+)(?:\s+(\S+))?(?:\s+no-reverse|\s+acl\s+\d+|\s+reversible)*'
            match = re.match(pattern2, processed_command)
            if match:
                name = match.group(1)
                protocol = match.group(2)
                global_ip = match.group(3)
                global_port = match.group(4).strip() if match.group(4) else 'any'
                inside_ip = match.group(5)
                inside_port = match.group(6).strip() if match.group(6) else 'any'

                # 还原带引号的标识符
                for i, quoted_name in enumerate(quoted_names):
                    placeholder = f"QUOTED_NAME_{i}"
                    if name == placeholder:
                        name = quoted_name

                result = {
                    'name': name,
                    'protocol': protocol,
                    'global_ip': global_ip,
                    'global_port': global_port,
                    'inside_ip': inside_ip,
                    'inside_port': inside_port,
                    'command': command
                }

        # 模式3: 两个标识符但没有protocol关键字 - nat server id1 id2 global ... inside ...
        if not result:
            pattern3 = r'nat server\s+(\S+)\s+(\S+)\s+global\s+(\S+)\s+inside\s+(\S+)(?:\s+no-reverse|\s+acl\s+\d+|\s+reversible)*'
            match = re.match(pattern3, processed_command)
            if match:
                id1 = match.group(1)
                global_ip = match.group(3)
                inside_ip = match.group(4)

                # 还原带引号的标识符
                for i, quoted_name in enumerate(quoted_names):
                    placeholder = f"QUOTED_NAME_{i}"
                    if id1 == placeholder:
                        id1 = quoted_name

                # 将第一个标识符作为名称
                name = id1

                result = {
                    'name': name,
                    'protocol': 'any',
                    'global_ip': global_ip,
                    'global_port': 'any',
                    'inside_ip': inside_ip,
                    'inside_port': 'any',
                    'command': command
                }

        # 模式4: 简化格式 - nat server id global ... inside ...
        if not result:
            pattern4 = r'nat server\s+(\S+)\s+global\s+(\S+)\s+inside\s+(\S+)(?:\s+no-reverse|\s+acl\s+\d+|\s+reversible)*'
            match = re.match(pattern4, processed_command)
            if match:
                name = match.group(1)
                global_ip = match.group(2)
                inside_ip = match.group(3)

                # 还原带引号的标识符
                for i, quoted_name in enumerate(quoted_names):
                    placeholder = f"QUOTED_NAME_{i}"
                    if name == placeholder:
                        name = quoted_name

                result = {
                    'name': name,
                    'protocol': 'any',
                    'global_ip': global_ip,
                    'global_port': 'any',
                    'inside_ip': inside_ip,
                    'inside_port': 'any',
                    'command': command
                }

        return result

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
                        # 直接使用原始命令进行解析，不再移除后缀
                        # 因为parse_huawei_command已经能处理这些情况
                        parsed = NATParser.parse_huawei_command(original_command)
                    else:  # h3c
                        parsed = NATParser.parse_h3c_command(line)

                    if parsed:
                        data.append(parsed)
                    else:
                        failed_entries.append(line)
                except Exception as e:
                    # 记录异常信息以便调试
                    print(f"解析错误: {line}, 异常: {str(e)}")
                    failed_entries.append(line)

        return data, failed_entries