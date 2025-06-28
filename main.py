
# -*- coding: utf-8 -*-

import os  
import json
import time
import subprocess
import datetime
from pathlib import Path
import re
import sys

# 只在直接从命令行运行时应用编码设置
# if sys.platform == "win32":
#     import codecs
#     sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
#     sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    
class TemperatureMonitor:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.data_file = self.config.get("data_file", "data.json")
        self.interval = self.config.get("interval_seconds", 5)
        self.monitor_components = self.config.get("monitor_components", {"cpu": True, "gpu": True})
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def get_cpu_temperature(self):
        """使用test_cpu_simple.py中的方法获取CPU温度"""
        try:
            result = subprocess.run(['wmic', 'path', 'win32_perfrawdata_counters_thermalzoneinformation', 'get', 'temperature'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    line = line.strip()
                    if line and line.isdigit():
                        temp_raw = float(line)
                        
                        if temp_raw > 2000:  # 开尔文*10格式
                            temp_kelvin = temp_raw / 10.0
                            temp_celsius = temp_kelvin - 273.15
                        elif temp_raw > 200:  # 开尔文格式
                            temp_celsius = temp_raw - 273.15
                        else:  # 摄氏度格式
                            temp_celsius = temp_raw
                        
                        if 0 < temp_celsius < 150:  # 合理的温度范围
                            return round(temp_celsius, 2)
        except Exception as e:
            print(f"获取CPU温度失败: {e}")
        
        return None
    
    def get_nvidia_gpu_temp_via_smi(self):
        """通过nvidia-smi获取NVIDIA GPU温度"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                temps = []
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line and line.replace('.', '').isdigit():
                        temp = float(line)
                        if 0 < temp < 150:
                            temps.append(temp)
                
                if temps:
                    return round(max(temps), 2)  # 返回最高温度
        except FileNotFoundError:
            # nvidia-smi 不存在
            pass
        except Exception as e:
            print(f"nvidia-smi获取GPU温度失败: {e}")
        
        return None
    
    def get_amd_gpu_temp_via_wmi(self):
        """通过WMI获取AMD GPU温度"""
        try:
            # 尝试获取AMD GPU传感器信息
            result = subprocess.run(['wmic', 'path', 'MSAcpi_ThermalZoneTemperature', 'get', 'CurrentTemperature'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    line = line.strip()
                    if line and line.isdigit():
                        # WMI温度通常是开尔文*10
                        temp_raw = float(line)
                        if temp_raw > 2000:
                            temp_celsius = (temp_raw / 10.0) - 273.15
                            if 0 < temp_celsius < 150:
                                return round(temp_celsius, 2)
        except Exception as e:
            print(f"WMI获取GPU温度失败: {e}")
        
        return None
    
    def get_gpu_temp_via_powershell(self):
        """通过PowerShell获取GPU温度"""
        try:
            # 使用PowerShell查询GPU温度
            ps_command = """
            Get-WmiObject -Namespace "root/OpenHardwareMonitor" -Class Sensor | 
            Where-Object {$_.SensorType -eq "Temperature" -and $_.Name -like "*GPU*"} | 
            Select-Object Value
            """
            
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout.strip():
                # 提取温度值
                matches = re.findall(r'(\d+(?:\.\d+)?)', result.stdout)
                if matches:
                    temps = [float(match) for match in matches if 0 < float(match) < 150]
                    if temps:
                        return round(max(temps), 2)
        except Exception as e:
            print(f"PowerShell获取GPU温度失败: {e}")
        
        return None
    
    def get_gpu_temp_via_wmic_gpu(self):
        """通过WMIC查询GPU信息"""
        try:
            # 查询显卡信息
            result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'name'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                print(f"检测到GPU: {gpu_info}")
                
                # 尝试查询温度传感器
                result2 = subprocess.run(['wmic', '/namespace:\\\\root\\wmi', 'path', 'MSAcpi_ThermalZoneTemperature', 'get', 'CurrentTemperature'], 
                                       capture_output=True, text=True, timeout=10)
                
                if result2.returncode == 0:
                    lines = result2.stdout.strip().split('\n')
                    for line in lines[1:]:
                        line = line.strip()
                        if line and line.isdigit():
                            temp_raw = float(line)
                            if temp_raw > 2000:
                                temp_celsius = (temp_raw / 10.0) - 273.15
                                if 30 < temp_celsius < 120:  # GPU合理温度范围
                                    return round(temp_celsius, 2)
        except Exception as e:
            print(f"WMIC GPU查询失败: {e}")
        
        return None
    
    def get_gpu_temperature(self):
        """获取GPU温度 - 尝试多种方法"""
        methods = [
            ("NVIDIA-SMI", self.get_nvidia_gpu_temp_via_smi),
            ("PowerShell", self.get_gpu_temp_via_powershell),
            ("WMI", self.get_amd_gpu_temp_via_wmi),
            ("WMIC", self.get_gpu_temp_via_wmic_gpu)
        ]
        
        for method_name, method_func in methods:
            try:
                temp = method_func()
                if temp is not None:
                    print(f"通过{method_name}获取到GPU温度: {temp}°C")
                    return temp
            except Exception as e:
                print(f"{method_name}方法失败: {e}")
                continue
        
        return None
    
    def collect_temperature_data(self):
        """收集温度数据"""
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "temperatures": {}
        }
        
        if self.monitor_components.get("cpu", False):
            cpu_temp = self.get_cpu_temperature()
            if cpu_temp is not None:
                data["temperatures"]["cpu"] = cpu_temp
                print(f"CPU温度: {cpu_temp}°C")
            else:
                print("无法获取CPU温度")
        
        if self.monitor_components.get("gpu", False):
            gpu_temp = self.get_gpu_temperature()
            if gpu_temp is not None:
                data["temperatures"]["gpu"] = gpu_temp
                print(f"GPU温度: {gpu_temp}°C")
            else:
                print("无法获取GPU温度 - 已尝试所有方法")
        
        return data
    
    def save_data(self, data):
        """保存数据到文件"""
        if not self.config.get("auto_save", True):
            return
        
        try:
            # 读取现有数据
            existing_data = []
            if Path(self.data_file).exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 添加新数据
            existing_data.append(data)
            
            # 保存数据
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def test_gpu_methods(self):
        """测试所有GPU温度获取方法"""
        print("=== 测试GPU温度获取方法 ===")
        
        methods = [
            ("NVIDIA-SMI", self.get_nvidia_gpu_temp_via_smi),
            ("PowerShell", self.get_gpu_temp_via_powershell),
            ("WMI", self.get_amd_gpu_temp_via_wmi),
            ("WMIC", self.get_gpu_temp_via_wmic_gpu)
        ]
        
        for method_name, method_func in methods:
            print(f"\n测试 {method_name} 方法:")
            try:
                temp = method_func()
                if temp is not None:
                    print(f"成功: {temp}°C")
                else:
                    print(f"未获取到温度")
            except Exception as e:
                print(f"错误: {e}")
    
    def run(self):
        """运行温度监控"""
        print(f"开始温度监控 (间隔: {self.interval}秒)")
        print(f"监控组件: {', '.join([k for k, v in self.monitor_components.items() if v])}")
        
        # 如果启用GPU监控，先测试GPU方法
        if self.monitor_components.get("gpu", False):
            self.test_gpu_methods()
        
        print("\n按 Ctrl+C 停止监控")
        
        try:
            while True:
                print(f"\n--- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
                
                # 收集温度数据
                data = self.collect_temperature_data()
                
                # 保存数据
                if data["temperatures"]:
                    self.save_data(data)
                
                # 等待下一次监控
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\n监控已停止")

if __name__ == "__main__":
    monitor = TemperatureMonitor()
    monitor.run()