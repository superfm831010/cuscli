import byzerllm


@byzerllm.prompt()
def _skill() -> str:
    """
    # Skill Specification: Teaching AI to Understand Your System

    ## What is a Skill?

    **Skill** is an instruction manual that teaches AI how to complete specific tasks.

    Imagine: you have a new colleague who is smart but unfamiliar with your system. How would you teach them?

    1. Tell them what the task is
    2. Show them the correct approach
    3. Warn them about common pitfalls
    4. Give them quick references

    A Skill is about writing these contents in a format that AI can understand.

    ## The Simplest Skill

    A Skill is just a folder containing a `SKILL.md` file:

    ```
    my-skill/
    └── SKILL.md
    ```

    `SKILL.md` looks like this:

    ```markdown
    ---
    name: my-skill
    description: One sentence explaining what this skill does
    ---

    # Skill Name

    Write specific content here...
    ```

    That's it!

    ## Structure of SKILL.md

    ### 1. Header Information (Required)

    ```yaml
    ---
    name: algorithm-types
    description: Distinguish between regression and classification algorithms, choose the correct base class and evaluation methods
    ---
    ```

    - `name`: Unique identifier for the skill (lowercase, hyphen-separated)
    - `description`: One-sentence explanation of purpose (AI uses this to decide whether to load)

    ### 2. Body Content (Free Form)

    The body is regular Markdown, write however you like. But some patterns are particularly effective:

    ## 5 Tips for Writing Good Skills

    ### Tip 1: Use Tables for Comparison

    ❌ Bad approach:
    > Regression algorithms output continuous values, use BaseRegression base class, evaluation metrics are RMSE, MSE, R2, MAE. Classification algorithms output discrete categories, use BaseClassification base class, evaluation metrics are F1, accuracy, etc.

    ✅ Good approach:

    | Type | Output | Base Class | Evaluation Metrics |
    |------|--------|------------|-------------------|
    | Regression | Continuous (23.5) | `BaseRegression` | RMSE, MSE, R2, MAE |
    | Classification | Discrete (0, 1, 2) | `BaseClassification` | F1, accuracy |

    **Why good?** Clear at a glance, no need to compare back and forth.

    ### Tip 2: Provide Copy-Paste Code

    ❌ Bad approach:
    > Use the vec_dense function to convert an array to a vector

    ✅ Good approach:

    ```sql
    select vec_dense(array(5.1, 3.5, 1.4, 0.2)) as features;
    ```

    **Why good?** AI can copy and use directly, no need to guess the format.

    ### Tip 3: Show Right vs Wrong Comparison

    ❌ Bad approach:
    > Don't use the training set for evaluation

    ✅ Good approach:

    ```sql
    -- ❌ Wrong: Evaluate using training set
    train train_data as LinearRegression.`/tmp/model` where
    evaluateTable="train_data";  -- This is the training set!

    -- ✅ Correct: Use independent evaluation set
    train train_data as LinearRegression.`/tmp/model` where
    evaluateTable="evaluate_data";  -- Independent evaluation set
    ```

    **Why good?** Wrong and correct side by side, memorable impression.

    ### Tip 4: Use Command Quick Reference Tables

    ❌ Bad approach:
    > You can use !show et to view all ETs, use !show et/Name to view examples, use !show et/params/Name to view parameters...

    ✅ Good approach:

    | I want to... | Command |
    |--------------|---------|
    | See available algorithms | `!show et;` |
    | See algorithm examples | `!show et/LinearRegression;` |
    | See algorithm parameters | `!show et/params/LinearRegression;` |
    | Kill a job | `!kill jobId;` |

    **Why good?** Start from the need, quickly find the answer.

    ### Tip 5: Summarize Key Points

    Add a Guidelines section at the end of the document:

    ```markdown
    ## Guidelines

    1. **Key point 1** - Brief explanation
    2. **Key point 2** - Brief explanation
    3. **Key point 3** - Brief explanation
    ```

    **Why good?** Quick review, reinforces memory.

    ## Complete Example

    Here is a complete Skill example:

    ```markdown
    ---
    name: quick-start
    description: Learn Byzer-SQL basics in 5 minutes
    ---

    # Quick Start

    Learn Byzer-SQL basics in 5 minutes.

    ## Load Data

    ```sql
    load csv.`/data/iris.csv` where header="true" as iris;
    ```

    ## Query Data

    ```sql
    select * from iris limit 10 as preview;
    ```

    ## Save Data

    ```sql
    save overwrite preview as parquet.`/output/iris`;
    ```

    ## Common Commands

    | I want to... | Command |
    |--------------|---------|
    | See data sources | `!show datasources;` |
    | See table list | `!show tables;` |

    ## Guidelines

    1. **Load before select** - Data must be loaded before querying
    2. **End with as tablename** - Every statement must name the result table
    3. **Use !show to explore** - When unsure, use !show to see what's available
    ```

    ## Skill Directory Structure

    Skills can be saved in two locations:

    ### 1. Project-level Skills (Default)

    Save in the current project's `.autocoderskills` directory:

    ```
    your-project/
    ├── .autocoderskills/
    │   ├── README.md           # Skill index
    │   ├── quick-start/
    │   │   └── SKILL.md
    │   ├── data-loading/
    │   │   └── SKILL.md
    │   └── machine-learning/
    │       └── SKILL.md
    └── src/
        └── ...
    ```

    ### 2. Global Skills

    If the user says "save as global skill", save in `~/.auto-coder/.autocoderskills` directory:

    ```
    ~/.auto-coder/
    └── .autocoderskills/
        ├── README.md           # Skill index
        ├── common-patterns/
        │   └── SKILL.md
        └── shared-utils/
            └── SKILL.md
    ```

    Global skills can be used across all projects.

    ### README.md Structure

    `README.md` lists all skills:

    ```markdown
    # Agent Skills

    | Skill | Description |
    |-------|-------------|
    | [quick-start](./quick-start/) | 5-minute intro |
    | [data-loading](./data-loading/) | Data loading |
    | [machine-learning](./machine-learning/) | Machine learning |
    ```

    ## Skill Writing Checklist

    After writing, check against this list:

    - [ ] Has `name` and `description` header info?
    - [ ] Does `description` make it clear what this skill does at a glance?
    - [ ] Used tables for comparison?
    - [ ] Code can be directly copied and run?
    - [ ] Showed wrong vs correct comparison?
    - [ ] Has quick reference table?
    - [ ] Has Guidelines summary at the end?

    ## One-Sentence Summary

    > **Skill = Header Info + Table Comparison + Copy-Paste Code + Wrong/Right Comparison + Quick Reference + Key Points**
    """
