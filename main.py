import ProcessGameState
# This is my filepath, you can change to whatever you want :)
MY_FILEPATH = "/Users/zhangshanrong/Desktop/game_state_frame_data.parquet"
# Define z-axis boundaries of the chokepoint
Z_MIN = 285
Z_MAX = 421
def main():
    gameState = ProcessGameState.ProcessGameState(MY_FILEPATH)

    # Q1 a. read the file
    print("Q1 a")
    gameState.show_the_data(5)

    # Q1 b. Return whether each row falls within a provided boundary
    gameState.is_within_boundary(Z_MIN, Z_MAX)
    gameState.add_boundary_check_column(Z_MIN, Z_MAX)
    num_within_boundary = gameState.data['within_boundary'].sum()
    print("Q1 b")
    print(f"There are {num_within_boundary} rows within the boundary")

    # Q1 c.Extract the weapon classes from the inventory json column
    gameState.extract_weapon_classes()
    print("Q1 c")
    print(gameState.data['weapon_classes'].head())

    # Q2 a Is entering via the light blue boundary a common strategy used by Team2 on T (terrorist) side?
    print("Q2 a")
    within_boundary_each_round = gameState.count_players_within_boundary_each_round('Team2', 'T')
    print(within_boundary_each_round[within_boundary_each_round > 0])
    """From the result, we can see that there is only one round for Team 2 with 2 players alive enter the chokepoint
        So, we can say that it is not a common strategy"""

    # Q2 b What is the average timer that Team2 on T(terrorist)side enter “BombsiteB” with least 2 rifles or SMGs?
    print("Q2 b")
    print(f"The average timer is {gameState.get_average_timer()}")
    """The average timer is 28.5625"""

    # Q2 c Using the same data set, tell our coaching staff where you suspect them to be waiting inside “BombsiteB”
    print("Q2 c")
    print(f"The top five points that are stayed by players are {gameState.draw_heatmap()}")





# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

