#!python
# -*- coding: utf-8 -*-
import os  
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from pathlib import Path
import sys

# 只在直接从命令行运行时应用编码设置
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

class TemperatureChartGenerator:
    def __init__(self, data_file="data.json"):
        self.data_file = data_file
        self.data = self.load_data()
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    
    def load_data(self):
        """加载温度数据"""
        try:
            if not Path(self.data_file).exists():
                print(f"数据文件 {self.data_file} 不存在")
                return []
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"成功加载 {len(data)} 条温度记录")
            return data
        except Exception as e:
            print(f"加载数据失败: {e}")
            return []
    
    def parse_data(self):
        """解析数据为时间序列"""
        timestamps = []
        cpu_temps = []
        gpu_temps = []
        
        for entry in self.data:
            try:
                # 解析时间戳
                timestamp = datetime.fromisoformat(entry['timestamp'])
                timestamps.append(timestamp)
                
                # 提取温度数据
                temperatures = entry.get('temperatures', {})
                
                # CPU温度
                cpu_temp = temperatures.get('cpu')
                cpu_temps.append(cpu_temp if cpu_temp is not None else np.nan)
                
                # GPU温度
                gpu_temp = temperatures.get('gpu')
                gpu_temps.append(gpu_temp if gpu_temp is not None else np.nan)
                
            except Exception as e:
                print(f"解析数据条目失败: {e}")
                continue
        
        return timestamps, cpu_temps, gpu_temps
    
    def create_temperature_chart(self, save_path="temperature_chart.png", show_chart=True):
        """创建温度趋势图"""
        if not self.data:
            print("没有数据可以绘制图表")
            return
        
        timestamps, cpu_temps, gpu_temps = self.parse_data()
        
        if not timestamps:
            print("没有有效的时间戳数据")
            return
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 绘制CPU温度曲线
        if any(not np.isnan(temp) for temp in cpu_temps):
            ax.plot(timestamps, cpu_temps, 'b-', linewidth=2, label='CPU温度', marker='o', markersize=4)
        
        # 绘制GPU温度曲线
        if any(not np.isnan(temp) for temp in gpu_temps):
            ax.plot(timestamps, gpu_temps, 'r-', linewidth=2, label='GPU温度', marker='s', markersize=4)
        
        # 设置图表标题和标签
        ax.set_title('温度监控趋势图', fontsize=16, fontweight='bold')
        ax.set_xlabel('时间', fontsize=12)
        ax.set_ylabel('温度 (°C)', fontsize=12)
        
        # 设置网格
        ax.grid(True, alpha=0.3)
        
        # 设置图例
        ax.legend(fontsize=12)
        
        # 格式化x轴时间显示
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        plt.xticks(rotation=45)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
        
        # 显示图表
        if show_chart:
            plt.show()
        
        plt.close()
    
    def create_statistics_chart(self, save_path="temperature_stats.png", show_chart=True):
        """创建温度统计图表"""
        if not self.data:
            print("没有数据可以绘制统计图表")
            return
        
        timestamps, cpu_temps, gpu_temps = self.parse_data()
        
        # 过滤有效数据
        valid_cpu_temps = [temp for temp in cpu_temps if not np.isnan(temp)]
        valid_gpu_temps = [temp for temp in gpu_temps if not np.isnan(temp)]
        
        if not valid_cpu_temps and not valid_gpu_temps:
            print("没有有效的温度数据")
            return
        
        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 温度分布直方图
        if valid_cpu_temps:
            ax1.hist(valid_cpu_temps, bins=20, alpha=0.7, color='blue', label='CPU')
        if valid_gpu_temps:
            ax1.hist(valid_gpu_temps, bins=20, alpha=0.7, color='red', label='GPU')
        ax1.set_title('温度分布直方图')
        ax1.set_xlabel('温度 (°C)')
        ax1.set_ylabel('频次')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 箱线图
        box_data = []
        box_labels = []
        if valid_cpu_temps:
            box_data.append(valid_cpu_temps)
            box_labels.append('CPU')
        if valid_gpu_temps:
            box_data.append(valid_gpu_temps)
            box_labels.append('GPU')
        
        if box_data:
            ax2.boxplot(box_data, labels=box_labels)
            ax2.set_title('温度箱线图')
            ax2.set_ylabel('温度 (°C)')
            ax2.grid(True, alpha=0.3)
        
        # 3. 温度统计表
        ax3.axis('tight')
        ax3.axis('off')
        
        stats_data = []
        if valid_cpu_temps:
            cpu_stats = [
                'CPU',
                f"{np.mean(valid_cpu_temps):.2f}",
                f"{np.min(valid_cpu_temps):.2f}",
                f"{np.max(valid_cpu_temps):.2f}",
                f"{np.std(valid_cpu_temps):.2f}",
                f"{len(valid_cpu_temps)}"
            ]
            stats_data.append(cpu_stats)
        
        if valid_gpu_temps:
            gpu_stats = [
                'GPU',
                f"{np.mean(valid_gpu_temps):.2f}",
                f"{np.min(valid_gpu_temps):.2f}",
                f"{np.max(valid_gpu_temps):.2f}",
                f"{np.std(valid_gpu_temps):.2f}",
                f"{len(valid_gpu_temps)}"
            ]
            stats_data.append(gpu_stats)
        
        if stats_data:
            columns = ['组件', '平均值(°C)', '最小值(°C)', '最大值(°C)', '标准差', '数据点数']
            table = ax3.table(cellText=stats_data,
                            colLabels=columns,
                            cellLoc='center',
                            loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            ax3.set_title('温度统计信息')
        
        # 4. 最近温度趋势
        recent_data = self.data[-20:] if len(self.data) > 20 else self.data
        recent_timestamps = []
        recent_cpu = []
        recent_gpu = []
        
        for entry in recent_data:
            try:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                recent_timestamps.append(timestamp)
                
                temperatures = entry.get('temperatures', {})
                recent_cpu.append(temperatures.get('cpu', np.nan))
                recent_gpu.append(temperatures.get('gpu', np.nan))
            except:
                continue
        
        if recent_timestamps:
            if any(not np.isnan(temp) for temp in recent_cpu):
                ax4.plot(recent_timestamps, recent_cpu, 'b-', marker='o', label='CPU')
            if any(not np.isnan(temp) for temp in recent_gpu):
                ax4.plot(recent_timestamps, recent_gpu, 'r-', marker='s', label='GPU')
            
            ax4.set_title('最近温度趋势')
            ax4.set_xlabel('时间')
            ax4.set_ylabel('温度 (°C)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
        
        plt.suptitle('温度监控统计报告', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"统计图表已保存到: {save_path}")
        
        # 显示图表
        if show_chart:
            plt.show()
        
        plt.close()
    
    def print_summary(self):
        """打印数据摘要"""
        if not self.data:
            print("没有数据")
            return
        
        timestamps, cpu_temps, gpu_temps = self.parse_data()
        
        valid_cpu_temps = [temp for temp in cpu_temps if not np.isnan(temp)]
        valid_gpu_temps = [temp for temp in gpu_temps if not np.isnan(temp)]
        
        print(f"\n=== 温度数据摘要 ===")
        print(f"数据记录总数: {len(self.data)}")
        print(f"时间范围: {timestamps[0].strftime('%Y-%m-%d %H:%M:%S')} 到 {timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if valid_cpu_temps:
            print(f"\nCPU温度:")
            print(f"  平均: {np.mean(valid_cpu_temps):.2f}°C")
            print(f"  最小: {np.min(valid_cpu_temps):.2f}°C")
            print(f"  最大: {np.max(valid_cpu_temps):.2f}°C")
            print(f"  数据点: {len(valid_cpu_temps)}")
        
        if valid_gpu_temps:
            print(f"\nGPU温度:")
            print(f"  平均: {np.mean(valid_gpu_temps):.2f}°C")
            print(f"  最小: {np.min(valid_gpu_temps):.2f}°C")
            print(f"  最大: {np.max(valid_gpu_temps):.2f}°C")
            print(f"  数据点: {len(valid_gpu_temps)}")
    
    def generate_all_charts(self):
        """生成所有图表"""
        print("正在生成温度趋势图...")
        self.create_temperature_chart(show_chart=False)
        
        print("正在生成统计图表...")
        self.create_statistics_chart(show_chart=False)
        
        self.print_summary()
        print("\n所有图表生成完成!")

def main():
    generator = TemperatureChartGenerator()
    
    print("温度数据图表生成器")
    print("1. 生成趋势图")
    print("2. 生成统计图表")
    print("3. 生成所有图表")
    print("4. 显示数据摘要")
    
    choice = input("请选择操作 (1-4): ").strip()
    
    if choice == "1":
        generator.create_temperature_chart()
    elif choice == "2":
        generator.create_statistics_chart()
    elif choice == "3":
        generator.generate_all_charts()
    elif choice == "4":
        generator.print_summary()
    else:
        print("无效选择")

if __name__ == "__main__":
    main()