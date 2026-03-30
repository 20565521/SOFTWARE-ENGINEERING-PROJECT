#!/usr/bin/env python3
"""Tkinter Expense Tracker GUI

Simple GUI for adding, listing, removing, totaling and exporting expenses.
Saves data to `expenses.json` next to this file.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")


@dataclass
class Expense:
	id: int
	date: str
	amount: float
	category: str
	description: str = ""


def load_expenses() -> List[Expense]:
	# New data format supports budgets and expenses. Migrate old list format if needed.
	if not os.path.exists(DATA_FILE):
		return []
	with open(DATA_FILE, "r", encoding="utf-8") as f:
		data = json.load(f)
	# old format: list of expenses
	if isinstance(data, list):
		return [Expense(**item) for item in data]
	# new format: dict with 'expenses' key
	items = data.get("expenses", [])
	return [Expense(**item) for item in items]


def save_expenses(items: List[Expense]) -> None:
	# When saving only expenses, try to preserve budgets if present.
	data = {}
	if os.path.exists(DATA_FILE):
		with open(DATA_FILE, "r", encoding="utf-8") as f:
			try:
				existing = json.load(f)
			except Exception:
				existing = {}
			if isinstance(existing, dict):
				data = existing
	data["expenses"] = [asdict(i) for i in items]
	with open(DATA_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=2, ensure_ascii=False)


def load_data() -> dict:
	if not os.path.exists(DATA_FILE):
		return {"expenses": [], "general_budget": None, "category_budgets": {}}
	with open(DATA_FILE, "r", encoding="utf-8") as f:
		try:
			data = json.load(f)
		except Exception:
			return {"expenses": [], "general_budget": None, "category_budgets": {}}
	if isinstance(data, list):
		return {"expenses": data, "general_budget": None, "category_budgets": {}}
	# ensure keys
	data.setdefault("expenses", [])
	data.setdefault("general_budget", None)
	data.setdefault("category_budgets", {})
	return data


def save_data(data: dict) -> None:
	with open(DATA_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=2, ensure_ascii=False)


def next_id(items: List[Expense]) -> int:
	return max((i.id for i in items), default=0) + 1


class ExpenseApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Expense Tracker")
		self.geometry("800x400")

		self.items: List[Expense] = []
		self.data = {"expenses": [], "general_budget": None, "category_budgets": {}}

		self._build_ui()
		self._load()

	def _build_ui(self) -> None:
		frm = ttk.Frame(self)
		frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

		left = ttk.Frame(frm)
		left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

		ttk.Label(left, text="Amount:").grid(row=0, column=0, sticky=tk.W)
		self.amount_var = tk.StringVar()
		ttk.Entry(left, textvariable=self.amount_var).grid(row=0, column=1)

		ttk.Label(left, text="Category:").grid(row=1, column=0, sticky=tk.W)
		self.category_var = tk.StringVar(value="misc")
		ttk.Entry(left, textvariable=self.category_var).grid(row=1, column=1)

		ttk.Label(left, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W)
		self.date_var = tk.StringVar(value=datetime.now().date().isoformat())
		ttk.Entry(left, textvariable=self.date_var).grid(row=2, column=1)

		ttk.Label(left, text="Description:").grid(row=3, column=0, sticky=tk.W)
		self.desc_var = tk.StringVar()
		ttk.Entry(left, textvariable=self.desc_var).grid(row=3, column=1)

		ttk.Button(left, text="Add", command=self.add_expense).grid(row=4, column=0, columnspan=2, pady=(8, 0))
		ttk.Button(left, text="Edit Selected", command=self.edit_selected).grid(row=5, column=0, columnspan=2, pady=(8, 0))
		ttk.Button(left, text="Remove Selected", command=self.remove_selected).grid(row=6, column=0, columnspan=2, pady=(8, 0))
		ttk.Button(left, text="Total", command=self.show_total).grid(row=7, column=0, columnspan=2, pady=(8, 0))
		ttk.Button(left, text="Export CSV", command=self.export_csv).grid(row=8, column=0, columnspan=2, pady=(8, 0))

		# Budget controls
		ttk.Separator(left, orient=tk.HORIZONTAL).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 8))
		ttk.Label(left, text="General Monthly Budget:").grid(row=10, column=0, sticky=tk.W)
		self.general_budget_var = tk.StringVar()
		ttk.Entry(left, textvariable=self.general_budget_var).grid(row=10, column=1)
		ttk.Button(left, text="Set General Budget", command=self.set_general_budget).grid(row=11, column=0, columnspan=2, pady=(4, 0))

		ttk.Label(left, text="Category: (for category budget)").grid(row=12, column=0, sticky=tk.W)
		self.cat_budget_category_var = tk.StringVar()
		ttk.Entry(left, textvariable=self.cat_budget_category_var).grid(row=12, column=1)
		ttk.Label(left, text="Amount:").grid(row=13, column=0, sticky=tk.W)
		self.cat_budget_amount_var = tk.StringVar()
		ttk.Entry(left, textvariable=self.cat_budget_amount_var).grid(row=13, column=1)
		ttk.Button(left, text="Set Category Budget", command=self.set_category_budget).grid(row=14, column=0, columnspan=2, pady=(4, 0))

		right = ttk.Frame(frm)
		right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		cols = ("id", "date", "amount", "category", "description")
		self.tree = ttk.Treeview(right, columns=cols, show="headings")
		for c in cols:
			self.tree.heading(c, text=c.title())
			if c == "description":
				self.tree.column(c, width=300)
			else:
				self.tree.column(c, width=80)
		self.tree.pack(fill=tk.BOTH, expand=True)

		self.status = ttk.Label(self, text="")
		self.status.pack(fill=tk.X)

	def _load(self) -> None:
		data = load_data()
		self.data = data
		self.items = [Expense(**e) for e in data.get("expenses", [])]
		self.refresh_tree()

		# populate budget fields if general budget exists for current month
		gb = self.data.get("general_budget")
		if gb and gb.get("month") == datetime.now().date().isoformat()[:7]:
			self.general_budget_var.set(str(gb.get("amount")))

	def refresh_tree(self) -> None:
		for r in self.tree.get_children():
			self.tree.delete(r)
		for i in self.items:
			self.tree.insert("", tk.END, values=(i.id, i.date, f"{i.amount:.2f}", i.category, i.description))
		# Update status to include budgets summary
		msgs = [f"{len(self.items)} expenses"]
		gb = self.data.get("general_budget")
		if gb:
			msgs.append(f"General budget: {gb.get('amount')} for {gb.get('month')}")
		cb = self.data.get("category_budgets", {})
		if cb:
			msgs.append(f"Category budgets: {len(cb)}")
		self.status.config(text=" | ".join(msgs))

	def add_expense(self) -> None:
		amt_s = self.amount_var.get().strip()
		try:
			amt = float(amt_s)
		except Exception:
			messagebox.showerror("Invalid amount", "Please enter a numeric amount.")
			return
		date = self.date_var.get().strip() or datetime.now().date().isoformat()
		cat = self.category_var.get().strip() or "misc"
		desc = self.desc_var.get().strip()
		# If editing an existing expense
		if hasattr(self, '_saved_id_for_edit') and getattr(self, '_saved_id_for_edit') is not None:
			rid = self._saved_id_for_edit
			for idx, it in enumerate(self.items):
				if it.id == rid:
					self.items[idx] = Expense(id=rid, date=date, amount=amt, category=cat, description=desc)
					break
			# clear edit flag
			self._saved_id_for_edit = None
		else:
			exp = Expense(id=next_id(self.items), date=date, amount=amt, category=cat, description=desc)
			self.items.append(exp)
		# persist via data dict
		self.data["expenses"] = [asdict(i) for i in self.items]
		save_data(self.data)
		self.refresh_tree()
		self.amount_var.set("")
		self.desc_var.set("")
		# Notify if hitting 90% of category budget for the month
		self.notify_if_threshold(exp)

	def notify_if_threshold(self, expense: Expense) -> None:
		month = expense.date[:7]
		cat = expense.category
		# total spent in this category for the month
		total = sum(e.amount for e in self.items if e.category == cat and e.date[:7] == month)
		cb = self.data.get("category_budgets", {})
		budget = None
		if isinstance(cb.get(cat), dict) and cb.get(cat).get("month") == month:
			budget = float(cb.get(cat).get("amount"))
		if budget is None:
			return
		if total >= 0.9 * budget:
			messagebox.showwarning("Budget alert", f"You have reached {total:.2f} which is >= 90% of your {cat} budget ({budget:.2f}) for {month}.")

	def remove_selected(self) -> None:
		sel = self.tree.selection()
		if not sel:
			messagebox.showinfo("Remove", "Select a row to remove.")
			return
		vals = self.tree.item(sel[0], "values")
		try:
			rid = int(vals[0])
		except Exception:
			messagebox.showerror("Error", "Unable to determine id of selected row.")
			return
		self.items = [i for i in self.items if i.id != rid]
		self.data["expenses"] = [asdict(i) for i in self.items]
		save_data(self.data)
		self.refresh_tree()

	def edit_selected(self) -> None:
		sel = self.tree.selection()
		if not sel:
			messagebox.showinfo("Edit", "Select a row to edit.")
			return
		vals = self.tree.item(sel[0], "values")
		try:
			rid = int(vals[0])
		except Exception:
			messagebox.showerror("Error", "Unable to determine id of selected row.")
			return
		# find expense
		exp = next((i for i in self.items if i.id == rid), None)
		if not exp:
			messagebox.showerror("Edit", "Expense not found.")
			return
		# populate fields for edit and change Add button to Save
		self.amount_var.set(str(exp.amount))
		self.category_var.set(exp.category)
		self.date_var.set(exp.date)
		self.desc_var.set(exp.description)
		# temporarily change Add to Save by binding Enter key and changing label not needed; we reuse Add to perform update if _saved_id_for_edit set
		self._saved_id_for_edit = rid

	def set_general_budget(self) -> None:
		amt_s = self.general_budget_var.get().strip()
		if not amt_s:
			messagebox.showinfo("General Budget", "Enter an amount.")
			return
		try:
			amt = float(amt_s)
		except Exception:
			messagebox.showerror("Invalid", "Enter numeric amount for general budget.")
			return
		month = datetime.now().date().isoformat()[:7]
		self.data["general_budget"] = {"amount": amt, "month": month}
		save_data(self.data)
		self.refresh_tree()
		messagebox.showinfo("General Budget", f"Set general budget to {amt:.2f} for {month}")

	def set_category_budget(self) -> None:
		cat = self.cat_budget_category_var.get().strip()
		amt_s = self.cat_budget_amount_var.get().strip()
		if not cat or not amt_s:
			messagebox.showinfo("Category Budget", "Enter category and amount.")
			return
		try:
			amt = float(amt_s)
		except Exception:
			messagebox.showerror("Invalid", "Enter numeric amount for category budget.")
			return
		month = datetime.now().date().isoformat()[:7]
		# ensure within general budget limits
		gb = self.data.get("general_budget")
		if gb and gb.get("month") == month:
			sum_cat = sum(float(v.get("amount")) for k, v in self.data.get("category_budgets", {}).items() if v.get("month") == month and k != cat)
			if sum_cat + amt > float(gb.get("amount")):
				messagebox.showerror("Limit", "Category budgets exceed general monthly budget.")
				return
		# set category budget
		self.data.setdefault("category_budgets", {})
		self.data["category_budgets"][cat] = {"amount": amt, "month": month}
		save_data(self.data)
		self.refresh_tree()
		messagebox.showinfo("Category Budget", f"Set budget for {cat}: {amt:.2f} for {month}")

	def show_total(self) -> None:
		total = sum(i.amount for i in self.items)
		messagebox.showinfo("Total", f"Total expenses: {total:.2f}")

	def export_csv(self) -> None:
		if not self.items:
			messagebox.showinfo("Export", "No expenses to export.")
			return
		path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv" )], initialfile="expenses_export.csv")
		if not path:
			return
		with open(path, "w", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow(["id", "date", "amount", "category", "description"])
			for i in self.items:
				writer.writerow([i.id, i.date, f"{i.amount:.2f}", i.category, i.description])
		messagebox.showinfo("Export", f"Exported {len(self.items)} rows to {path}")


def main() -> None:
	app = ExpenseApp()
	app.mainloop()


if __name__ == "__main__":
	main()