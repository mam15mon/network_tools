# 标准库导入
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

def clean_build_files() -> None:
    """清理构建文件"""
    print("\n🧹 清理构建文件...")

    # 清理目录
    for dir_name in ['dist', 'build', '__pycache__']:
        if os.path.exists(dir_name):
            print(f"   删除目录: {dir_name}")
            shutil.rmtree(dir_name)

    # 清理spec文件
    for spec_file in glob.glob('*.spec'):
        print(f"   删除文件: {spec_file}")
        os.remove(spec_file)

    # 清理所有 __pycache__ 目录
    for root, _, _ in os.walk('.'):
        cache_dir = Path(root) / '__pycache__'
        if cache_dir.exists():
            print(f"   删除缓存: {cache_dir}")
            shutil.rmtree(cache_dir)

def normalize_package_name(name):
    """标准化包名，处理常见的格式差异"""
    # 转换为小写
    name = name.lower()
    # 替换下划线为连字符（PyPI通常使用连字符，但有些包使用下划线）
    name = name.replace('_', '-')
    # 移除常见的包名前缀
    prefixes = ['python-']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name

def parse_requirement(req_str):
    """解析需求字符串，分离包名和版本信息"""
    # 处理各种版本说明符: ==, >=, <=, >, <, ~=, !=
    for operator in ['==', '>=', '<=', '>', '<', '~=', '!=']:
        if operator in req_str:
            parts = req_str.split(operator, 1)
            return normalize_package_name(parts[0].strip()), parts[1].strip()

    # 没有版本说明符
    return normalize_package_name(req_str.strip()), None

def get_installed_packages() -> Dict[str, str]:
    """获取已安装的包列表"""
    try:
        # 使用pip list --format=json获取更准确的包信息
        output = subprocess.check_output([
            sys.executable,
            "-m",
            "pip",
            "list",
            "--format=json"
        ]).decode()

        packages = json.loads(output)
        return {normalize_package_name(pkg['name']): pkg['version'] for pkg in packages}
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        # 如果JSON格式不可用，回退到文本解析
        output = subprocess.check_output([
            sys.executable,
            "-m",
            "pip",
            "list"
        ]).decode().split('\n')

        return {
            normalize_package_name(line.split()[0]): line.split()[1]
            for line in output[2:]
            if len(line.split()) >= 2
        }

def install_package(package: str) -> None:
    """安装指定的包"""
    print(f"正在安装 {package}...")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "-i",
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        package
    ])

def install_requirements() -> None:
    """安装必要的依赖"""
    print("检查依赖...")

    # 获取已安装的包列表
    installed_packages = get_installed_packages()

    # 从requirements.txt读取依赖
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    # 添加构建所需的额外依赖
    if "pyinstaller" not in [parse_requirement(req)[0] for req in requirements]:
        requirements.append("pyinstaller")

    # 检查所有依赖
    missing_packages = []
    outdated_packages = []

    for req in requirements:
        pkg_name, pkg_version = parse_requirement(req)

        if pkg_name not in installed_packages:
            # 包不存在
            missing_packages.append(req)
        elif pkg_version and installed_packages[pkg_name] != pkg_version:
            # 版本不匹配
            outdated_packages.append((pkg_name, installed_packages[pkg_name], pkg_version, req))

    # 显示依赖状态摘要
    if not missing_packages and not outdated_packages:
        print("✅ 所有依赖已安装且版本匹配")
    else:
        if missing_packages:
            print(f"\n⚠️ 缺少 {len(missing_packages)} 个依赖:")
            for pkg in missing_packages:
                print(f"  - {pkg}")

            # 询问是否安装缺少的依赖
            response = input("\n是否安装缺少的依赖? (y/n): ")
            if response.lower() == 'y':
                for pkg in missing_packages:
                    install_package(pkg)
            else:
                print("⚠️ 警告: 缺少依赖可能导致构建失败")

        if outdated_packages:
            print(f"\n⚠️ {len(outdated_packages)} 个依赖版本不匹配:")
            for pkg_name, current_ver, required_ver, req in outdated_packages:
                print(f"  - {pkg_name}: 当前 {current_ver}, 需要 {required_ver}")

            # 询问是否更新版本不匹配的依赖
            response = input("\n是否更新这些依赖? (y/n): ")
            if response.lower() == 'y':
                for _, _, _, req in outdated_packages:
                    install_package(req)
            else:
                print("⚠️ 警告: 依赖版本不匹配可能导致构建问题")

    # 确保PyInstaller已安装
    if "pyinstaller" not in installed_packages:
        print("\n⚠️ PyInstaller未安装，这是构建所必需的")
        response = input("是否安装PyInstaller? (y/n): ")
        if response.lower() == 'y':
            install_package("pyinstaller")
        else:
            print("❌ 错误: 没有PyInstaller无法继续构建")
            sys.exit(1)

def setup_upx() -> bool:
    """设置UPX压缩器"""
    upx_dir = Path('upx')

    # 如果UPX目录已存在，则认为已设置
    if upx_dir.exists() and (upx_dir / 'upx.exe').exists():
        print("✅ UPX已设置")
        return True

    print("⚙️ 正在设置UPX压缩器...")

    # 创建UPX目录
    upx_dir.mkdir(exist_ok=True)

    # UPX下载URL
    upx_version = "4.2.1"
    upx_url = f"https://github.com/upx/upx/releases/download/v{upx_version}/upx-{upx_version}-win64.zip"

    try:
        import urllib.request
        import zipfile

        # 下载UPX
        print(f"📥 正在下载UPX {upx_version}...")
        zip_path = upx_dir / "upx.zip"
        urllib.request.urlretrieve(upx_url, zip_path)

        # 解压UPX
        print("📦 正在解压UPX...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('.exe') or file.endswith('.txt'):
                    # 提取文件名
                    filename = os.path.basename(file)
                    # 解压到UPX目录
                    source = zip_ref.open(file)
                    target = open(upx_dir / filename, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)

        # 删除下载的ZIP文件
        zip_path.unlink()

        print("✅ UPX设置完成")
        return True
    except Exception as e:
        print(f"❌ UPX设置失败: {str(e)}")
        return False

def verify_and_convert_icon() -> str:
    """验证图标文件并返回路径"""
    # 检查resources/icons目录中的图标
    icon_paths = [
        Path('resources/icons/app.ico'),
        Path('resources/icons/network.png')
    ]

    for icon_path in icon_paths:
        if icon_path.exists():
            return str(icon_path)

    print("警告: 未找到图标文件，将使用默认图标")
    return None

def get_pyinstaller_args() -> List[str]:
    """获取 PyInstaller 参数列表"""
    args = [
        'src/main.py',  # 主程序文件
        '--name=network_tools',  # 英文名称
        '--windowed',  # 无控制台窗口
        '--noconfirm',  # 覆盖现有文件
        '--clean',  # 清理临时文件
        # '--onedir',  # 生成目录而不是单个文件，便于调试
        '--onefile',  # 生成单个exe文件
        '--log-level=INFO',  # 日志级别

        # UPX压缩设置
        '--upx-dir=upx',  # UPX目录
        '--upx',  # 启用UPX压缩
        '--upx-exclude=vcruntime140.dll',  # 排除特定文件不压缩
        '--upx-exclude=python*.dll',
        '--upx-exclude=ucrtbase.dll',
        '--upx-exclude=VCRUNTIME140.dll',
        '--upx-exclude=msvcp140.dll',
    ]

    # 添加图标
    icon_path = verify_and_convert_icon()
    if icon_path:
        args.append(f'--icon={icon_path}')

    # 添加资源文件
    args.extend([
        '--add-data=resources;resources',  # 添加resources目录
        '--add-data=src/templates;src/templates',  # 添加templates目录
    ])

    # 添加依赖包
    args.extend([
        '--collect-all=openpyxl',
        '--collect-all=jinja2',
        '--collect-all=requests',
    ])

    # 添加调试选项
    args.extend([
        '--debug=imports',  # 调试导入问题
        '--debug=bootloader',  # 调试启动加载器
    ])

    # 显式导入关键模块
    args.extend([
        # PyQt6相关
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtCore.QObject',
        '--hidden-import=PyQt6.QtCore.pyqtSignal',
        '--hidden-import=PyQt6.QtCore.QMetaObject',
        '--hidden-import=PyQt6.QtCore.Qt',
        '--hidden-import=PyQt6.QtCore.Q_ARG',
        '--hidden-import=PyQt6.QtGui',
        # 其他依赖
        '--hidden-import=openpyxl',
        '--hidden-import=jinja2',
        '--hidden-import=ipaddress',
        '--hidden-import=re',
        '--hidden-import=json',
        '--hidden-import=subprocess',
        '--hidden-import=threading',
        '--hidden-import=asyncio',
        '--hidden-import=requests',
        # 项目模块
        '--hidden-import=src',
        '--hidden-import=src.utils',
        '--hidden-import=src.utils.ip_utils',
        '--hidden-import=src.utils.text_utils',
        '--hidden-import=src.utils.nat_parser',
        '--hidden-import=src.utils.logger',
        '--hidden-import=src.utils.async_utils',
        '--hidden-import=src.gui',
        '--hidden-import=src.gui.tabs',
        '--hidden-import=src.gui.tabs.__init__',
        '--hidden-import=src.gui.tabs.subnet_calculator_tab',
        '--hidden-import=src.gui.tabs.ip_calculator_tab',
        '--hidden-import=src.gui.tabs.route_summary_tab',
        '--hidden-import=src.gui.tabs.mask_converter_tab',
        '--hidden-import=src.gui.tabs.nat_parser_tab',
        '--hidden-import=src.gui.tabs.vsr_config_tab',
        '--hidden-import=src.gui.tabs.network_analyzer_tab',
    ])

    return args

def copy_to_release(exe_name: str) -> None:
    """复制文件到发布目录"""
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)

    # 单文件模式
    src_exe_path = Path('dist') / f"{exe_name}.exe"

    if src_exe_path.exists():
        print(f"复制可执行文件: {src_exe_path} -> {release_dir}")
        shutil.copy2(src_exe_path, release_dir)
    else:
        raise FileNotFoundError(f"生成文件 {src_exe_path} 不存在，请检查构建日志")

def check_gh_cli() -> bool:
    """检查是否安装了GitHub CLI"""
    try:
        # 首先检查gh命令
        result = subprocess.run(["gh", "--version"], capture_output=True)
        return True
    except FileNotFoundError:
        print("❌ 未找到GitHub CLI工具，正在检查安装状态...")
        try:
            # 检查是否已通过winget安装
            result = subprocess.run(
                ["winget", "list", "--name", "GitHub"],
                capture_output=True,
                text=True
            )

            if "GitHub CLI" in result.stdout:
                print("💡 GitHub CLI 已经安装，但可能需要重启终端或重启电脑")
                print("   请尝试:")
                print("   1. 关闭当前终端，打开新终端")
                print("   2. 如果还不行，请重启电脑")
                print("   3. 重启后运行 'gh auth login' 进行身份验证")
            else:
                print("❌ GitHub CLI 未安装。请使用以下命令安装:")
                print("   winget install GitHub.cli")
                print("\n安装后:")
                print("   1. 关闭当前终端，打开新终端")
                print("   2. 运行 'gh auth login' 进行身份验证")
        except FileNotFoundError:
            print("❌ 未找到 winget 命令。请手动安装 GitHub CLI:")
            print("   1. 访问: https://cli.github.com/")
            print("   2. 下载并安装GitHub CLI")
            print("   3. 运行 'gh auth login' 进行身份验证")
        return False

def publish_to_github(version: str = None, title: str = None, notes: str = None, draft: bool = False, pre_release: bool = False) -> bool:
    """将构建好的文件发布到GitHub

    Args:
        version: 版本号，例如 v0.1.1
        title: 发布标题，如果不指定则使用版本号
        notes: 发布说明，如果不指定则使用默认文本
        draft: 是否创建为草稿版本
        pre_release: 是否标记为预发布版本
    """
    print("\n🚀 发布到GitHub...")

    # 检查gh命令行工具
    if not check_gh_cli():
        return False

    # 确保release目录中有可执行文件
    exe_path = Path('release') / 'network_tools.exe'

    if not exe_path.exists():
        print("❌ 错误: 找不到要发布的可执行文件")
        return False

    try:
        # 获取所有标签
        tags = subprocess.check_output(["git", "tag"]).decode().split()

        # 如果没有指定版本号，列出现有版本并要求输入
        if not version:
            if tags:
                print("\n现有版本:")
                for tag in sorted(tags):
                    print(f"  {tag}")

            while True:
                version = input("\n请输入新的版本号 (例如 v0.1.1): ").strip()
                if not version:
                    print("❌ 版本号不能为空")
                    continue
                if not version.startswith('v'):
                    print("❌ 版本号必须以 'v' 开头")
                    continue
                if version in tags:
                    print(f"❌ 版本 {version} 已存在")
                    continue
                break

        # 如果没有指定标题，使用默认标题
        if not title:
            title = f"网络工具集 {version}"

        # 如果没有指定说明，使用默认说明
        if not notes:
            notes = f"网络工具集 {version} 发布版本"

        # 创建版本标签
        print(f"📌 创建标签 {version}...")
        subprocess.run(["git", "tag", version], check=True)
        subprocess.run(["git", "push", "origin", version], check=True)

        # 构建发布命令
        cmd = [
            "gh", "release", "create",
            version,
            "--title", title,
            "--notes", notes,
        ]

        # 添加可选参数
        if draft:
            cmd.append("--draft")
        if pre_release:
            cmd.append("--prerelease")

        # 添加文件
        cmd.append(str(exe_path))

        # 创建发布
        print("📦 创建发布版本...")
        subprocess.run(cmd, check=True)

        print(f"✅ 成功发布 {version} 到GitHub")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 发布失败: 命令执行错误 - {str(e)}")
        # 清理失败的tag
        try:
            subprocess.run(["git", "tag", "-d", version])
            subprocess.run(["git", "push", "origin", ":refs/tags/" + version])
            print(f"🧹 已清理失败的标签 {version}")
        except:
            pass
        return False
    except Exception as e:
        print(f"❌ 发布失败: {str(e)}")
        return False

def build_exe() -> None:
    """构建可执行文件"""
    # 确保安装了依赖
    install_requirements()

    # 清理旧的release目录
    if os.path.exists('release'):
        shutil.rmtree('release')

    # 设置UPX压缩器
    setup_upx()

    # 添加版本信息
    version_info = {
        'version': '1.0.0',
        'company_name': 'Network Tools',
        'file_description': '网络工具集',
        'internal_name': 'network_tools',
        'legal_copyright': 'Copyright (c) 2025',
        'original_filename': 'network_tools.exe',
        'product_name': '网络工具集',
    }

    # 创建版本文件
    version_file = 'version_info.txt'
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write('# UTF-8\n')
        f.write('#\n')
        f.write('# For more details about fixed file info \'ffi\' see:\n')
        f.write('# http://msdn.microsoft.com/en-us/library/ms646997.aspx\n')
        f.write('VSVersionInfo(\n')
        f.write('  ffi=FixedFileInfo(\n')
        f.write('    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)\n')
        f.write('    # Set not needed items to zero 0.\n')
        f.write('    filevers=(1, 0, 0, 0),\n')
        f.write('    prodvers=(1, 0, 0, 0),\n')
        f.write('    # Contains a bitmask that specifies the valid bits \'flags\'\n')
        f.write('    mask=0x3f,\n')
        f.write('    # Contains a bitmask that specifies the Boolean attributes of the file.\n')
        f.write('    flags=0x0,\n')
        f.write('    # The operating system for which this file was designed.\n')
        f.write('    # 0x4 - NT and there is no need to change it.\n')
        f.write('    OS=0x40004,\n')
        f.write('    # The general type of file.\n')
        f.write('    # 0x1 - the file is an application.\n')
        f.write('    fileType=0x1,\n')
        f.write('    # The function of the file.\n')
        f.write('    # 0x0 - the function is not defined for this fileType\n')
        f.write('    subtype=0x0,\n')
        f.write('    # Creation date and time stamp.\n')
        f.write('    date=(0, 0)\n')
        f.write('    ),\n')
        f.write('  kids=[\n')
        f.write('    StringFileInfo(\n')
        f.write('      [\n')
        f.write('      StringTable(\n')
        f.write('        u\'080404b0\',\n')
        f.write('        [StringStruct(u\'CompanyName\', u\'{}\'),\n'.format(version_info['company_name']))
        f.write('        StringStruct(u\'FileDescription\', u\'{}\'),\n'.format(version_info['file_description']))
        f.write('        StringStruct(u\'FileVersion\', u\'{}\'),\n'.format(version_info['version']))
        f.write('        StringStruct(u\'InternalName\', u\'{}\'),\n'.format(version_info['internal_name']))
        f.write('        StringStruct(u\'LegalCopyright\', u\'{}\'),\n'.format(version_info['legal_copyright']))
        f.write('        StringStruct(u\'OriginalFilename\', u\'{}\'),\n'.format(version_info['original_filename']))
        f.write('        StringStruct(u\'ProductName\', u\'{}\'),\n'.format(version_info['product_name']))
        f.write('        StringStruct(u\'ProductVersion\', u\'{}\')])\n'.format(version_info['version']))
        f.write('      ]),\n')
        f.write('    VarFileInfo([VarStruct(u\'Translation\', [2052, 1200])])\n')
        f.write('  ]\n')
        f.write(')\n')

    # 运行 PyInstaller
    try:
        # pylint: disable=import-outside-toplevel
        import PyInstaller.__main__

        # 添加版本文件参数
        args = get_pyinstaller_args()
        args.append(f'--version-file={version_file}')

        PyInstaller.__main__.run(args)
    except ImportError:
        print("错误: 未能导入 PyInstaller，请确保已正确安装")
        sys.exit(1)
    finally:
        # 清理版本文件
        if os.path.exists(version_file):
            os.remove(version_file)

    # 复制到发布目录
    copy_to_release('network_tools')

    # 清理构建文件
    clean_build_files()

    print("\n🎉 构建完成！发布包在 release 目录中")

    # 询问是否发布
    response = input("\n是否发布到GitHub? (y/n): ")
    if response.lower() == 'y':
        version = input("输入版本号 (例如 v1.0.0): ")
        publish_to_github(version)

if __name__ == '__main__':
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == 'build':
            build_exe()
        elif sys.argv[1] == 'publish':
            # 获取可选参数
            version = None
            title = None
            notes = None
            draft = False
            pre_release = False

            # 解析参数
            i = 2
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg == '--version':
                    i += 1
                    if i < len(sys.argv):
                        version = sys.argv[i]
                elif arg == '--title':
                    i += 1
                    if i < len(sys.argv):
                        title = sys.argv[i]
                elif arg == '--notes':
                    i += 1
                    if i < len(sys.argv):
                        notes = sys.argv[i]
                elif arg == '--draft':
                    draft = True
                elif arg == '--pre-release':
                    pre_release = True
                i += 1

            publish_to_github(version, title, notes, draft, pre_release)
        elif sys.argv[1] == 'all':
            build_exe()
            publish_to_github()
        else:
            print("用法:")
            print("  python build.py build          - 仅构建")
            print("  python build.py publish        - 仅发布")
            print("  python build.py all           - 构建并发布")
            print("\n发布参数:")
            print("  --version <版本号>            - 指定版本号")
            print("  --title <标题>               - 指定发布标题")
            print("  --notes <说明>               - 指定发布说明")
            print("  --draft                     - 创建为草稿版本")
            print("  --pre-release               - 标记为预发布版本")
    else:
        # 默认行为：仅构建
        build_exe()
