class JSONLDAnalyzer:

    def analyze(
        self,
        json_ld: list[dict],
    ):

        types = []

        valid_blocks = 0
        invalid_blocks = 0

        for block in json_ld:

            if not isinstance(
                block,
                dict
            ):

                invalid_blocks += 1
                continue

            valid_blocks += 1

            block_type = block.get(
                "@type"
            )

            if isinstance(
                block_type,
                list
            ):

                types.extend(
                    str(item)
                    for item in block_type
                )

            elif block_type:

                types.append(
                    str(block_type)
                )

        unique_types = sorted(
            set(types)
        )

        return {
            "check": "json_ld",
            "status": (
                "present"
                if valid_blocks > 0
                else "missing"
            ),
            "evidence": {
                "total_blocks": len(
                    json_ld
                ),
                "valid_blocks": valid_blocks,
                "invalid_blocks": invalid_blocks,
                "types": unique_types,
            },
        }