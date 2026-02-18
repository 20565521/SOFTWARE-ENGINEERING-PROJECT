#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <ctime>

using namespace std;

struct Expense {
    string date;
    string category;
    double amount;
    string description;
};

class ExpenseTracker {
private:
    vector<Expense> expenses;
    const string filename = "expenses.txt";

public:
    ExpenseTracker() {
        loadExpenses();
    }

    void addExpense() {
        Expense exp;
        
        cout << "\n=== Add New Expense ===" << endl;
        
        // Get current date
        time_t now = time(0);
        tm* ltm = localtime(&now);
        cout << "Date (YYYY-MM-DD) [default: ";
        cout << (1900 + ltm->tm_year) << "-" 
             << setfill('0') << setw(2) << (1 + ltm->tm_mon) << "-"
             << setw(2) << ltm->tm_mday << "]: ";
        setfill(' ');
        
        getline(cin, exp.date);
        if (exp.date.empty()) {
            stringstream ss;
            ss << (1900 + ltm->tm_year) << "-" 
               << setfill('0') << setw(2) << (1 + ltm->tm_mon) << "-"
               << setw(2) << ltm->tm_mday;
            exp.date = ss.str();
        }
        
        cout << "Category (Food, Transport, Entertainment, Utilities, Other): ";
        getline(cin, exp.category);
        
        cout << "Amount: $";
        string amountStr;
        getline(cin, amountStr);
        exp.amount = stod(amountStr);
        
        cout << "Description: ";
        getline(cin, exp.description);
        
        expenses.push_back(exp);
        saveExpenses();
        
        cout << "\n✓ Expense added successfully!" << endl;
    }

    void viewExpenses() {
        if (expenses.empty()) {
            cout << "\nNo expenses recorded yet." << endl;
            return;
        }
        
        cout << "\n=== All Expenses ===" << endl;
        cout << left << setw(12) << "Date" 
             << setw(15) << "Category" 
             << setw(12) << "Amount" 
             << "Description" << endl;
        cout << string(60, '-') << endl;
        
        double total = 0;
        for (size_t i = 0; i < expenses.size(); i++) {
            cout << left << setw(12) << expenses[i].date
                 << setw(15) << expenses[i].category
                 << "$" << setw(10) << fixed << setprecision(2) << expenses[i].amount
                 << expenses[i].description << endl;
            total += expenses[i].amount;
        }
        
        cout << string(60, '-') << endl;
        cout << "Total: $" << fixed << setprecision(2) << total << endl;
    }

    void viewByCategory() {
        if (expenses.empty()) {
            cout << "\nNo expenses recorded yet." << endl;
            return;
        }
        
        cout << "\n=== Expenses by Category ===" << endl;
        
        vector<string> categories;
        for (const auto& exp : expenses) {
            if (find(categories.begin(), categories.end(), exp.category) == categories.end()) {
                categories.push_back(exp.category);
            }
        }
        
        double totalExpenses = 0;
        for (const auto& cat : categories) {
            double categoryTotal = 0;
            for (const auto& exp : expenses) {
                if (exp.category == cat) {
                    categoryTotal += exp.amount;
                }
            }
            totalExpenses += categoryTotal;
            cout << left << setw(20) << cat << "$" << fixed << setprecision(2) << categoryTotal << endl;
        }
        
        cout << "\nTotal Expenses: $" << fixed << setprecision(2) << totalExpenses << endl;
    }

    void viewByDateRange() {
        if (expenses.empty()) {
            cout << "\nNo expenses recorded yet." << endl;
            return;
        }
        
        string startDate, endDate;
        cout << "\n=== View by Date Range ===" << endl;
        cout << "Start date (YYYY-MM-DD): ";
        getline(cin, startDate);
        cout << "End date (YYYY-MM-DD): ";
        getline(cin, endDate);
        
        double total = 0;
        cout << "\nExpenses from " << startDate << " to " << endDate << ":" << endl;
        cout << left << setw(12) << "Date" 
             << setw(15) << "Category" 
             << setw(12) << "Amount" 
             << "Description" << endl;
        cout << string(60, '-') << endl;
        
        bool found = false;
        for (const auto& exp : expenses) {
            if (exp.date >= startDate && exp.date <= endDate) {
                cout << left << setw(12) << exp.date
                     << setw(15) << exp.category
                     << "$" << setw(10) << fixed << setprecision(2) << exp.amount
                     << exp.description << endl;
                total += exp.amount;
                found = true;
            }
        }
        
        if (!found) {
            cout << "No expenses found in this date range." << endl;
        } else {
            cout << string(60, '-') << endl;
            cout << "Total: $" << fixed << setprecision(2) << total << endl;
        }
    }

    void deleteExpense() {
        viewExpenses();
        
        if (expenses.empty()) return;
        
        cout << "\nEnter the row number to delete (1-" << expenses.size() << "): ";
        int index;
        cin >> index;
        cin.ignore();
        
        if (index > 0 && index <= expenses.size()) {
            expenses.erase(expenses.begin() + index - 1);
            saveExpenses();
            cout << "✓ Expense deleted successfully!" << endl;
        } else {
            cout << "Invalid index!" << endl;
        }
    }

private:
    void saveExpenses() {
        ofstream file(filename);
        for (const auto& exp : expenses) {
            file << exp.date << "|" << exp.category << "|" 
                 << exp.amount << "|" << exp.description << "\n";
        }
        file.close();
    }

    void loadExpenses() {
        ifstream file(filename);
        if (!file.is_open()) {
            return; // File doesn't exist yet
        }
        
        string line;
        while (getline(file, line)) {
            if (line.empty()) continue;
            
            size_t pos1 = line.find('|');
            size_t pos2 = line.find('|', pos1 + 1);
            size_t pos3 = line.find('|', pos2 + 1);
            
            Expense exp;
            exp.date = line.substr(0, pos1);
            exp.category = line.substr(pos1 + 1, pos2 - pos1 - 1);
            exp.amount = stod(line.substr(pos2 + 1, pos3 - pos2 - 1));
            exp.description = line.substr(pos3 + 1);
            
            expenses.push_back(exp);
        }
        file.close();
    }
};

void displayMenu() {
    cout << "\n╔════════════════════════════════╗" << endl;
    cout << "║   EXPENSE TRACKER SYSTEM       ║" << endl;
    cout << "╠════════════════════════════════╣" << endl;
    cout << "║ 1. Add Expense                 ║" << endl;
    cout << "║ 2. View All Expenses           ║" << endl;
    cout << "║ 3. View by Category            ║" << endl;
    cout << "║ 4. View by Date Range          ║" << endl;
    cout << "║ 5. Delete Expense              ║" << endl;
    cout << "║ 6. Exit                        ║" << endl;
    cout << "╚════════════════════════════════╝" << endl;
    cout << "Enter your choice (1-6): ";
}

int main() {
    ExpenseTracker tracker;
    int choice;
    
    cout << "Welcome to Expense Tracker!" << endl;
    
    while (true) {
        displayMenu();
        cin >> choice;
        cin.ignore();
        
        switch (choice) {
            case 1:
                tracker.addExpense();
                break;
            case 2:
                tracker.viewExpenses();
                break;
            case 3:
                tracker.viewByCategory();
                break;
            case 4:
                tracker.viewByDateRange();
                break;
            case 5:
                tracker.deleteExpense();
                break;
            case 6:
                cout << "\nThank you for using Expense Tracker. Goodbye!" << endl;
                return 0;
            default:
                cout << "\nInvalid choice! Please try again." << endl;
        }
    }
    
    return 0;
}