import re
from typing import List, Tuple, Union
from netaddr import IPRange, IPNetwork, AddrFormatError

class TextUtils:
    # 掩码转换说明文本
    MASK_CONVERTER_HELP = """支持以下格式：
1. CIDR格式：192.168.1.0/24
2. 掩码格式：192.168.1.0 255.255.255.0
3. 单个IP（默认/32）：192.168.1.1

可以使用以下方式分隔多个条目：
- 换行
- 逗号 (,)
- 分号 (;)"""

    # 路由汇总说明文本
    ROUTE_SUMMARY_HELP = """支持以下格式：
1. CIDR格式：192.168.1.0/24
2. IP范围格式：
   - 完整格式：192.168.1.1-192.168.1.254
   - 简化格式：1.1.1.0-255
3. 单个IP：192.168.1.1

可以使用以下方式分隔多个条目：
- 换行
- 逗号 (,)
- 分号 (;)

汇总模式说明：
- 精确汇总：保证汇总后的网段完全匹配原始网段，不会包含额外的IP地址
- 非精确汇总：寻找包含所有输入网段的最小CIDR块，可能会包含额外的IP地址，但能得到最简单的汇总结果"""

    @staticmethod
    def split_text(text: str) -> List[str]:
        """
        将输入文本按多种分隔符拆分为列表
        支持换行符、逗号、分号等分隔符
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 处理后的文本列表
        """
        if not text.strip():
            return []
        
        # 首先按换行符分割
        lines = text.split('\n')
        
        entries = []
        for line in lines:
            # 跳过空行
            if not line.strip():
                continue
            
            # 按逗号、分号分割每一行（支持中文标点）
            items = [e.strip() for e in re.split(r'[,，;；]', line)]
            
            # 添加非空条目
            entries.extend(item for item in items if item)
            
        return entries

    @staticmethod
    def parse_ip_range(entry: str) -> Union[IPRange, IPNetwork, None]:
        """
        解析IP范围文本
        支持以下格式：
        1. IP范围完整格式：1.1.1.1-1.1.1.25
        2. IP范围简化格式：1.1.1.1-25
        3. CIDR格式：1.1.1.0/24
        4. 单个IP：1.1.1.1
        
        Args:
            entry: IP范围文本
            
        Returns:
            Union[IPRange, IPNetwork]: 解析后的IP范围对象
            
        Raises:
            ValueError: 解析失败时抛出异常
        """
        entry = entry.strip()
        if not entry:
            return None
        
        try:
            # 处理IP范围格式
            if '-' in entry:
                parts = entry.split('-')
                if len(parts) != 2:
                    raise ValueError("IP范围格式错误，应为：1.1.1.1-25 或 1.1.1.1-1.1.1.25")
                
                start, end = parts
                start = start.strip()
                end = end.strip()
                
                # 如果起始IP不完整，报错提示
                if start.count('.') != 3:
                    raise ValueError("起始IP地址必须是完整的IP地址，如：1.1.1.1")
                
                # 处理简化格式 (如 1.1.1.1-25)
                if '.' not in end:
                    try:
                        end_num = int(end)
                        if end_num < 0 or end_num > 255:
                            raise ValueError("IP地址最后一位必须在0-255之间")
                        prefix = '.'.join(start.split('.')[:-1])
                        end = f"{prefix}.{end}"
                    except ValueError:
                        raise ValueError(f"无效的IP范围结尾: {end}")
                
                try:
                    return IPRange(start, end)
                except AddrFormatError as e:
                    raise ValueError(f"无效的IP范围: {start}-{end}")
                    
            # 处理CIDR格式或单个IP
            else:
                if '/' not in entry:
                    entry += '/32'
                return IPNetwork(entry)
                
        except Exception as e:
            raise ValueError(
                f"无效的路由条目: {entry}\n"
                f"支持的格式：\n"
                f"1. IP范围完整格式：1.1.1.1-1.1.1.25\n"
                f"2. IP范围简化格式：1.1.1.1-25\n"
                f"3. CIDR格式：1.1.1.0/24\n"
                f"4. 单个IP：1.1.1.1\n"
                f"错误详情：{str(e)}"
            )
