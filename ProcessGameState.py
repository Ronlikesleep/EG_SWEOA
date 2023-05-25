import json

import pandas as pd


Z_MIN = 285
Z_MAX = 421


class ProcessGameState:

    def __init__(self, filepath):
        # Read the parquet file
        self.data = pd.read_parquet("/Users/zhangshanrong/Desktop/game_state_frame_data.parquet", engine='pyarrow')

    def show_the_data(self, num_rows):
        return self.data.head(num_rows)

    def is_point_in_triangle(pt, v1, v2, v3):
        # Barycentric technique
        alpha = ((v2[1] - v3[1]) * (pt[0] - v3[0]) + (v3[0] - v2[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        beta = ((v3[1] - v1[1]) * (pt[0] - v3[0]) + (v1[0] - v3[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        gamma = 1.0 - alpha - beta
        return alpha > 0 and beta > 0 and gamma > 0

    def is_point_in_quadrilateral(pt, v1, v2, v3, v4):
        # For a point to be in a quadrilateral, it has to be in one of the two triangles that make up the quadrilateral
        return ProcessGameState.is_point_in_triangle(pt, v1, v2, v3) or ProcessGameState.is_point_in_triangle(pt, v1,
                                                                                                              v3, v4)

    def is_point_on_line(pt, v1, v2):
        if pt == v1 or pt == v2:
            return False

        # Calculate slope of the line
        m = (v1[1] - v2[1]) / (v1[0] - v2[0])

        # Calculate y-coordinate of the point if it was on the line
        y = m * (pt[0] - v1[0]) + v1[1]

        # Return True if the actual y-coordinate is close enough to the calculated y-coordinate
        return abs(y - pt[1]) < 1e-6

    def is_within_boundary(self, z_min, z_max):
        # Define triangle and quadrilateral coordinates
        tri_coords = [(-1735, 250), (-2024, 398), (-1565, 580)]  # Points 13, 14, 17
        quad_coords = [(-2024, 398), (-2806, 742), (-2472, 1233), (-1565, 580)]  # Points 14, 15, 16, 17
        line_coords = [(-2024, 398), (-1565, 580)]  # Points 14, 17
        # Apply the checks to each row
        within_boundary = self.data.apply(lambda row: (z_min <= row['z'] <= z_max) and \
                        (ProcessGameState.is_point_in_quadrilateral((row['x'], row['y']),*quad_coords) or \
                        ProcessGameState.is_point_in_triangle((row['x'], row['y']),*tri_coords) or \
                        ProcessGameState.is_point_on_line((row['x'], row['y']),*line_coords)), axis=1)
        return within_boundary

    def add_boundary_check_column(self, Z_MIN, Z_MAX):
        self.data['within_boundary'] = self.is_within_boundary(Z_MIN, Z_MAX)




a = ProcessGameState("/Users/zhangshanrong/Desktop/game_state_frame_data.parquet")

# filtered_data = a.data[a.data['inventory'].notna()]
# c = a.is_within_boundary(Z_MIN, Z_MAX)

a.data.to_excel("/Users/zhangshanrong/Desktop/1.xlsx", engine='openpyxl', index=False)
#print(a['weapon_classes'].head())
