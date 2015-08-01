/*Time is running out. You have a final match to play as a counter terrorist.
You have N players each having a distinct ID from 1 to N. You have to choose
some players on your team from these N players such that no two chosen players
have consecutive numbers (as they tend to kill each other). Also you definitely
have to choose some K players whose numbers are given. They are the snipers.
Find the maximum number of players that you can choose.*/

#include <cmath>
#include <cstdio>
#include <vector>
#include <iostream>
#include <algorithm>
using namespace std;

int main() {
	int n, k, id1=1, id2=1, players=1;
	cin >> n >> k;
	int sniper_array[k];
	for (int i = 0; i < k; i++)  {
		cin >> sniper_array[i];
	}
	std::sort(sniper_array, sniper_array + sizeof sniper_array / sizeof sniper_array[0]);
	
	if (sniper_array[0] == 1 || sniper_array[0] == 2) players = 0;
	
	for (int i = 0; i<k; i++) {
		id1 = sniper_array[i];
		if (id1 - id2 >= 4) {
			players += (id1-id2)/2;
		}
		else {
			players += 1;
		}
		id2 = id1;
	}
	players += (n-id1)/2;
	cout << players;
    return 0;
}
