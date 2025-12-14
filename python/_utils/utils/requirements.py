# %%
# akes 2 requirement files and updates the target with any missing libraries in the updated source file
def merge_requirements(targetFile, sourceFile):
    import os

    print(os.getcwd())

    targetFileReqs = {}
    with open(targetFile) as f:
        lines = f.readlines()

        for line in lines:
            key = line.strip().split("==")[0]
            value = f";{line.strip().split(';')[-1]}" if ";" in line else ""
            # print(key, value)
            targetFileReqs[key] = value
        # targetFileReqs = {line.strip().split('==')[0]: "==".join(line.strip().split('==')[1:]) for line in lines}
    print("target:", targetFileReqs)

    sourceFileReqs = {}
    with open(sourceFile) as f:
        lines = f.readlines()
        # sourceFileReqs = {line.strip().split('==')[0]: "==".join(line.strip().split('==')[1:]) for line in lines}
        for line in lines:
            key = line.strip().split("==")[0]
            value = f";{line.strip().split(';')[-1]}" if ";" in line else ""
            # print(key, value)
            sourceFileReqs[key] = value
    print("source:", sourceFileReqs)

    for k, v in sourceFileReqs.items():
        if k not in targetFileReqs and k not in ["psycopg", "psycopg-binary"]:
            print("new:", k, v)
            targetFileReqs[k] = v

    print("-" * 100)
    print("new requirements:", targetFileReqs)

    with open(targetFile, "w") as f:
        for k, v in targetFileReqs.items():
            line = f"{k}{v}\n"
            print(line)
            f.write(line)
