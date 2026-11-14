# PLAN ĐÃ LÀM

## Mục tiêu

Xây module Kakuro độc lập, theo OOP, dễ ghép launcher sau này. Dùng đúng hai bảng HTML làm dữ liệu chuẩn.

Đã chốt: PySide6, UI trình diễn, Backtracking + Forward checking, MRV, Degree và LCV.

## Thiết kế

- Mỗi ô trắng là biến, domain ban đầu {1,…,9}.
- Mỗi dãy ngang/dọc có tổng bằng clue; các số trong dãy không trùng.
- Tách lớp dữ liệu bảng, mô hình CSP, solver và UI. Solver không phụ thuộc PySide6.
- Cung cấp KakuroWidget(parent=None) cho launcher; hỗ trợ chạy bằng python -m task_3.
- Chuyển dữ liệu hai bảng sang cấu trúc Python rõ ràng; giữ nguyên HTML tham chiếu.

## Solver và UI

- Chọn biến bằng MRV; hòa thì dùng Degree, rồi tọa độ.
- Xếp giá trị bằng LCV theo số giá trị bị loại khỏi domain lân cận; hòa thì chọn số nhỏ.
- Forward checking loại giá trị vi phạm không trùng hoặc khiến tổng dãy không thể đạt.
- Backtracking khôi phục đầy đủ assignment và domain khi nhánh thất bại.
- Phát sự kiện chọn biến, thử số, thu hẹp domain, thất bại, khôi phục và hoàn tất.
- UI hiển thị domain trong ô, dãy đang xét, lý do cập nhật và log thuật toán.
- Có chọn đề, chạy, tạm dừng, bước tiếp, tốc độ và đặt lại. Không chặn event loop.
- Dùng trắng, xám, đen như mẫu; không gradient. Vẽ đường chéo clue trực tiếp.

---

# FINAL PROJECT - ĐỀ BÀI

## Course: Introduction to Artificial Intelligence

### Task 1 (3pts): Local Search & Propositional Logic

#### Descriptions: N-queen problem

---

### Task 2 (3pts): Adversarial Search

#### Descriptions: Tank Battle Game

---

### Task 3: Constraint Satisfaction Problems (Do only this one)

#### Descriptions: Kakuro

- Students are expected to familiarize themselves with the rules and gameplay of Kakuro by referring to the Kakuro article on Wikipedia <https://en.wikipedia.org/wiki/Kakuro>.
- Given the example Kakuro game board shown below, students are required to formulate the game as a Constraint Satisfaction Problem (CSP) by identifying the variables, their corresponding domains, and the constraints governing the puzzle. <Final_Project_AI\task_3\kakuro_demo.html>
- Students should then develop a solver that combines constraint propagation techniques with Backtracking Search to find a valid solution. The implementation should incorporate appropriate heuristic techniques introduced in Lecture 08 to improve the efficiency of the search process.

#### Requirements:

- _1. (1pt)_: Formulate the given problem correctly as a `Constraint Satisfaction
Problem (CSP)`, clearly identifying and explaining the relevant components, including variables, domains, and constraints. Describe and justify the algorithms and techniques applied in the project.
- _2. (1pt)_: Implement a solver capable of finding a valid solution to the given problem. Demonstrate and evaluate the solver’s correctness, stability, and effectiveness by applying it to the more complex test case provided below <Final_Project_AI\task_3\kakuro_task.html>
- _3. (1pt)_: Implement a user interface _(UI)_ for the game that clearly visualizes the domains of variables, the constraint propagation process, and the Backtracking Search process.

#### Notice:

- The project must be designed and implemented following **Object-Oriented
  Programming principles**.
- The evaluation configurations: macOS 13.7.8 (Ventura) with an Intel Core i5 processor

---

### Yêu cầu thêm

#### Thuật toán

_Lecture 8: Constraint Satisfaction Problems_

#### 1. AC-3 algorithm

pseudocode
function AC-3(csp)
returns false if an inconsistency is found and true otherwise
inputs: csp, a binary CSP with components (X, D, C)
local variables: queue, a queue of arcs, initially all the arcs in csp
while queue is not empty do
(Xi , Xj) ← REMOVE-FIRST(queue)
if REVISE(csp, Xi , Xj) then
if size of Di = 0 then return false
for each Xk in Xi.NEIGHBORS - {Xj} do
add (Xk , Xi) to queue
return true

function REVISE(csp, Xi , Xj)
returns true iff we revise the domain of Xi
revised ← false
for each x in Di do
if no value y in Dj allows (x ,y) to satisfy the constraint between Xi and Xj then
delete x from Di
revised ← true
return revised

- The worst-case complexity is 𝑂(𝑐𝑑^3)
  - 𝑛: number of variables, each has domain size 𝑑, 𝑐 binary constraints (arc)

#### 2. Backtracking Search

- States are defined by the values assigned so far
  - Initial state: empty assignment { }
  - Successor function: assign a value to an unassigned variable that agrees with the current assignment → fail if no legal assignments
  - Goal test: the current assignment is complete
- Depth-first search: choose values for one variable at a time and backtrack when a variable has no legal values left

pseudocode
function BACKTRACKING-SEARCH(csp) returns a solution, or failure
return BACKTRACK({ }, csp)

function BACKTRACK(assignment, csp) returns a solution, or failure
if assignment is complete then return assignment
var ← SELECT-UNASSIGNED-VARIABLE(csp)
for each value in ORDER-DOMAIN-VALUES(var, assignment, csp) do
if value is consistent with assignment then
add {var = value} to assignment
inferences ← INFERENCE(csp, var, value)
if inferences != failure then
add inferences to assignment
result ← BACKTRACK(assignment, csp)
if result != failure then
return result
remove {var = value} and inferences from assignment
return failure

#### 3. Variable and value ordering (Heuristics)

- 1. Minimum-remaining-values (MRV) heuristic: choose the variable with the fewest legal values.
- 2. Degree heuristic (DH): choose the variable that involves in the largest number of constraints on other unassigned variables.
- 3. Least constraining value (LCV) heuristic: given a variable, choose the value that leaves the maximum flexibility for subsequent variable assignments
- 4. Inference: Forward checking
- Keep track of remaining legal values for unassigned variables
  Terminate search when any variable has no legal values

#### 4. MIN-CONFLICTS algorithm

pseudocode
function MIN-CONFLICTS(csp, max steps) returns a solution or failure
inputs: csp, a constraint satisfaction problem
max steps, the number of steps allowed before giving up
current ← an initial complete assignment for csp
for i = 1 to max steps do
if current is a solution for csp then return current
var ← a randomly chosen conflicted variable from csp.VARIABLES
value ← the value v for var that minimizes CONFLICTS(var, v, current, csp)
set var = value in current
return failure
