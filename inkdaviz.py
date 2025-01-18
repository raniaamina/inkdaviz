import inkex
import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import re


class Inkdaviz(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--name", type=str, help="Main Tab")
        pars.add_argument("--csv_file", type=str, help="Path to the CSV file")
        pars.add_argument("--chart_type", type=str, choices=["pie", "donut", "bar", "line", "table"], help="Type of chart to generate")
        pars.add_argument("--title", type=str, default="", help="Title of the chart")
        pars.add_argument("--x_label", type=str, default="", help="Label for the X-axis")
        pars.add_argument("--y_label", type=str, default="", help="Label for the Y-axis")
        pars.add_argument("--color_palette", type=str, choices=["default", "pastel", "vibrant"], default="default", help="Color palette for the chart")
        pars.add_argument("--width", type=float, default=10, help="Width of the chart in inches")
        pars.add_argument("--height", type=float, default=6, help="Height of the chart in inches")
        pars.add_argument("--unit", type=str, choices=["in", "cm", "px"], default="in", help="Unit of measurement for width and height")

    def convert_to_inches(self, value, unit):
            if unit == "in":
                return value
            elif unit == "cm":
                return value / 2.54  # Convert cm to inches
            elif unit == "px":
                return value / 96  # Convert pixels to inches (assuming 96 DPI)
            else:
                return value

    def effect(self):
        self.color_palettes = {
            "default": ['#0D6EFD', '#6610F2', '#6F42C1', '#D63384', '#DC3545', '#FD7E14', '#FFC107', '#4AB563', '#20C997', '#3CB1C3'],
            "pastel": ['#81B4FE', '#AF83F8', '#B49DDF', '#EA95BF', '#ED969E', '#FEBC85', '#FFDF7E', '#8FD19E', '#8BE3C9', '#86CFDA'],
            "vibrant": ['#073984', '#35087E', '#3A2264', '#6F1B45', '#721C24', '#84420A', '#856404', '#155724', '#11694F', '#0C5460']
        }
        self.color_palette = self.color_palettes.get(self.options.color_palette, self.color_palettes['default'])

        if not self.options.csv_file:
            inkex.errormsg("Please choose a CSV File.")
            return

        if not os.path.isfile(self.options.csv_file):
            inkex.errormsg("CSV Not Found.")
            return

        result = self.read_csv(self.options.csv_file)
        if not result:
            return

        headers, rows = result
        x_label = self.options.x_label if self.options.x_label in headers else headers[0]
        if not self.options.x_label: 
            self.options.x_label = headers[0]

        if not self.options.y_label:
            y_columns = [header for header in headers if header != x_label]
        else:
            y_columns = [header.strip() for header in self.options.y_label.split(",") if header.strip() in headers]
        
        if not y_columns:
            inkex.errormsg(f"Y Axis Label '{self.options.y_label}' not found in CSV.")
            return

        x_data = [row[headers.index(x_label)] for row in rows]
        y_data_sets = [[row[headers.index(y_col)] for row in rows] for y_col in y_columns]

        if self.options.x_label and self.options.x_label not in headers:
            inkex.errormsg(f"X Axis Label '{self.options.x_label}' not found in CSV. Using default: '{x_label}'.")

        fig, ax = plt.subplots(figsize=(self.convert_to_inches(self.options.width, self.options.unit), self.convert_to_inches(self.options.height, self.options.unit)))
        
        if self.options.chart_type == "pie":
            self.generate_pie_chart(ax, x_data, *y_data_sets)  
        elif self.options.chart_type == "donut":
            self.generate_donut_chart(ax, x_data, *y_data_sets)
        elif self.options.chart_type == "bar":
            self.generate_bar_chart(ax, x_data, *y_data_sets)  
        elif self.options.chart_type == "line":
            self.generate_line_chart(ax, x_data, *y_data_sets)  
        elif self.options.chart_type == "table":
            self.generate_table(ax, [headers] + rows)
        else:
            inkex.errormsg("Invalid chart type.")
            return

        if self.options.chart_type != "pie":
            plt.title(self.options.title, fontsize=18, fontweight='bold')
        svg_data = self.fig_to_svg(fig)
        self.import_svg_to_document(svg_data)


    def read_csv(self, file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = [row for row in reader]
                if not data or len(data[0]) < 2:
                    inkex.errormsg("CSV file must have at least two columns.")
                    return None
                headers = data[0]
                rows = data[1:]
                return headers, rows
        except Exception as e:
            inkex.errormsg(f"Error reading CSV file: {e}")
            return None

    def generate_pie_chart(self, ax, x_data, *y_data_sets):
        if not y_data_sets or not x_data:
            inkex.utils.debug("Error: No valid data for pie charts.")
            return

        num_charts = len(y_data_sets)
        chart_height = 1.0
        gap = 0.1

        ax.axis('off')

        plt.title(
            self.options.title,
            fontsize=18,
            fontweight='bold',
            loc='center',  
            y=2.3 
        )

        for idx, y_data in enumerate(y_data_sets):
            if len(x_data) != len(y_data):
                inkex.utils.debug(f"Error: The length of X data and Y data do not match for chart {idx + 1}. X length: {len(x_data)}, Y length: {len(y_data)}")
                continue

            labels = [str(x_val) for x_val in x_data]
            sizes = []

            for y_val in y_data:
                try:
                    size = float(y_val)
                    sizes.append(size)
                except ValueError:
                    inkex.utils.debug(f"Error: '{y_val}' is invalid for chart {idx + 1}, ignoring this data.")
                    continue

            if sizes:
                total = sum(sizes)
                sub_ax = ax.figure.add_axes([0.1, 0.9 - (idx * (chart_height + gap)), 0.8, chart_height])
                sub_ax.axis('equal')

                wedges, _ = sub_ax.pie(
                    sizes,
                    labels=None,
                    startangle=90,
                    colors=self.color_palette
                )

                for i, wedge in enumerate(wedges):
                    angle = (wedge.theta1 + wedge.theta2) / 2
                    x = wedge.r * 0.6 * np.cos(np.radians(angle))
                    y = wedge.r * 0.6 * np.sin(np.radians(angle))

                    percentage = (sizes[i] / total) * 100

                    sub_ax.text(
                        x,
                        y,
                        f"{y_data[i]} ({percentage:.1f}%)",
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black'
                    )

                    label_y = y - 0.03
                    sub_ax.text(
                        x,
                        label_y,
                        labels[i],
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black')

                header_name = self.options.y_label.split(",")[idx] if idx < len(self.options.y_label.split(",")) else f"Dataset {idx + 1}"

                if header_name not in labels and header_name != self.options.title:
                    sub_ax.text(
                        0.5, 0, header_name,
                        ha='center', va='center', fontsize=10, fontweight='bold', transform=sub_ax.transAxes
                    )
                else:
                    inkex.utils.debug(f"Skipping header generation for chart {idx + 1} as header_name matches the title or x_data.")
            else:
                inkex.utils.debug(f"Error: No valid data for pie chart {idx + 1}.")



    def generate_donut_chart(self, ax, x_data, *y_data_sets):
        if len(x_data) != len(y_data_sets[0]):
            inkex.utils.debug(f"Error: The length of X data and Y data do not match.")
            return

        y_headers = self.options.y_label.split(",")
        base_radius = 1.2  
        width = 0.55
        offset = 0.75 

        label_colors = {label: self.color_palette[i % len(self.color_palette)] for i, label in enumerate(x_data)}

        for i, y_data in enumerate(y_data_sets):
            sizes = []
            for y_val in y_data:
                try:
                    size = float(y_val)
                    sizes.append(size)
                except ValueError:
                    inkex.utils.debug(f"Error: '{y_val}' is invalid, ignoring this data.")
                    continue

            if sizes:
                wedges, texts = ax.pie(
                    sizes,
                    labels=None,
                    startangle=90,
                    colors=[label_colors[label] for label in x_data],
                    wedgeprops={'width': width, 'edgecolor': 'white'},
                    radius=base_radius + (i * offset) 
                )

                for wedge, size, label in zip(wedges, sizes, x_data):
                    angle = (wedge.theta2 + wedge.theta1) / 2.0
                    x_center = (base_radius + (i * offset) - width / 2)  * np.cos(np.radians(angle))
                    y_center = (base_radius + (i * offset) - width / 2)  * np.sin(np.radians(angle))

                    total = sum(sizes)
                    percentage = (size / total) * 100

                    ax.text(x_center, y_center, f"{int(size)}\n({percentage:.1f}%)", ha='center', va='center', fontsize=10, color='black')

                    y_label_offset = y_center - 0.2
                    ax.text(x_center, y_label_offset, label, ha='center', va='center', fontsize=8, color='black')

                header_position = base_radius + (i * offset) + width / 2

                angle_start = np.mean([wedge.theta1 for wedge in wedges])
                angle_end = np.mean([wedge.theta2 for wedge in wedges])
                x_header = (base_radius + (i * offset) + width / 2) * np.cos(np.radians((angle_start + angle_end) / 2))
                y_header = (base_radius + (i * offset) + width / 2) * np.sin(np.radians((angle_start + angle_end) / 2))

                ax.text(
                    0,
                    base_radius + (i * offset) + 0.1,
                    y_headers[i] if i < len(y_headers) else f"Dataset {i + 1}",
                    ha='center',
                    va='center',
                    fontsize=12,
                    color='black'
                )
            else:
                inkex.utils.debug(f"Error: No valid data for donut chart (Y set {i}).")
        ax.axis('equal')



    def generate_bar_chart(self, ax, labels, *value_sets):
        try:
            value_sets = [[float(value) for value in values] for values in value_sets]
        except ValueError as e:
            inkex.errormsg(f"Error converting Y values to numbers: {e}")
            return

        if labels and any(value_sets):
            bar_width = 0.35
            x_indices = range(len(labels))
            series_labels = self.options.y_label.split(",") if self.options.y_label else [f"Series {i+1}" for i in range(len(value_sets))]

            for i, (values, series_label) in enumerate(zip(value_sets, series_labels)):
                offset = bar_width * i
                ax.bar(
                    [x + offset for x in x_indices],
                    values,
                    width=bar_width,
                    color=self.color_palette[i % len(self.color_palette)],
                    label=series_label 
                )

            ax.set_xticks([x + bar_width * (len(value_sets) - 1) / 2 for x in x_indices])
            ax.set_xticklabels(labels)
            ax.set_xlabel(self.options.x_label)
            # ax.set_ylabel(self.options.y_label)
            ax.legend()
            ax.grid(True, axis='y', linestyle='--', linewidth=0.5)
        else:
            inkex.errormsg("Error: No valid data for bar chart.")

    def generate_line_chart(self, ax, labels, *value_sets):
        try:
            value_sets = [[float(value) for value in values] for values in value_sets]
        except ValueError as e:
            inkex.errormsg(f"Error converting Y values to numbers: {e}")
            return

        if labels and any(value_sets):
            y_headers = self.options.y_label.split(",")  
            for i, (values, header) in enumerate(zip(value_sets, y_headers)):
                ax.plot(
                    labels,
                    values,
                    color=self.color_palette[i % len(self.color_palette)],
                    marker='o',
                    label=header if i < len(y_headers) else f"Series {i+1}"
                )

                for x, y in zip(labels, values):
                    try:
                        if isinstance(y, (int, float)):
                            ax.text(float(x), float(y), f"{str(y)}", ha='center', va='bottom', fontsize=8, color=self.color_palette[i % len(self.color_palette)])
                    except ValueError:
                        pass

            ax.set_xlabel(self.options.x_label)
            # ax.set_ylabel(self.options.y_label)
            
            ax.grid(True, axis='y', linestyle='--', linewidth=0.5)
            
            ax.legend()
        else:
            inkex.errormsg("Error: No valid data for line chart.")

    def generate_table(self, ax, data):
        ax.axis('off')
        
        headers = data[0]  
        rows = data[1:]  
        
        x_label = self.options.x_label.strip()
        x_label_index = headers.index(x_label) if x_label in headers else None

        if not self.options.y_label:
            selected_headers = headers
        else:
            y_labels = [header.strip() for header in self.options.y_label.split(",")]
            selected_headers = [header for header in headers if header in y_labels]
        
        if x_label_index is not None and x_label not in selected_headers:
            selected_headers.insert(0, x_label)
        
        if not selected_headers:
            raise ValueError("No valid headers found for the table.")

        selected_indices = [headers.index(header) for header in selected_headers]

        filtered_data = [[row[idx] for idx in selected_indices] for row in rows]
        filtered_data.insert(0, selected_headers)  

        table = ax.table(cellText=filtered_data, loc='center', cellLoc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        header_color = self.color_palette[0]

        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Header
                cell.set_fontsize(10)
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor(header_color)
                cell.set_height(0.06)
            else:  # Data
                cell.set_height(0.05)




    def fig_to_svg(self, fig):
        output = BytesIO()
        fig.savefig(output, format='svg')
        plt.close(fig)
        return output.getvalue().decode('utf-8')

    def import_svg_to_document(self, svg_data):
        try:
            svg_data = svg_data.replace('<style type="text/css">*{stroke-linejoin: round; stroke-linecap: butt}</style>', '')

            if isinstance(svg_data, bytes):
                svg_data = svg_data.decode('utf-8')

            match = re.search(r'(<svg.*?>.*?</svg>)', svg_data, re.DOTALL)
            
            if match:
                svg_data_cleaned = match.group(1)
            else:
                inkex.utils.debug("Error: Unable to find valid SVG.")
                return

            svg_data_cleaned = svg_data_cleaned

            svg_document = inkex.load_svg(svg_data_cleaned)

            self.document.getroot().append(svg_document.getroot())

            # inkex.utils.debug("SVG Chart Imported!")
            
        except Exception as e:
            inkex.utils.debug(f"Error when importing SVG: {e}")

if __name__ == '__main__':
    Inkdaviz().run()