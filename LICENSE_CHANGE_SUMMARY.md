# License Change Summary

## Overview
The Glyph Forge client has been converted from a proprietary license to the **Apache License 2.0**, making it fully open source.

## What Changed

### 1. LICENSE File
- **Before**: Proprietary "Glyph Client License Agreement" with usage restrictions
- **After**: Full Apache License 2.0 text with copyright notice for Devpro LLC

### 2. pyproject.toml Metadata
- **Before**:
  ```toml
  classifiers = [
    "License :: Other/Proprietary License",
  ]
  license = { text = "Glyph Client License Agreement" }
  ```
- **After**:
  ```toml
  classifiers = [
    "License :: OSI Approved :: Apache Software License",
  ]
  license = { text = "Apache-2.0" }
  ```

### 3. README.md
- Updated license section to include full Apache 2.0 notice and copyright statement
- Added link to LICENSE file

### 4. NOTICE File (New)
- Created NOTICE file as per Apache 2.0 best practices
- Includes copyright and attribution information
- Added to distribution in pyproject.toml

## Apache 2.0 License Benefits

The Apache License 2.0 provides:

✅ **Permissive Use**: Anyone can use, modify, and distribute the code
✅ **Commercial Friendly**: Can be used in commercial projects
✅ **Patent Protection**: Explicit grant of patent rights from contributors
✅ **Attribution**: Requires attribution notices to be preserved
✅ **Clear Terms**: Well-established, legally vetted license text

## What This Means

### For Users
- ✓ Free to use for any purpose (personal, commercial, etc.)
- ✓ Can modify and create derivative works
- ✓ Can redistribute the software
- ✓ Explicit patent grant protects against patent claims
- ✓ Must include copyright notice and license when redistributing

### For Contributors
- ✓ Contributions automatically licensed under Apache 2.0
- ✓ Clear terms for collaboration
- ✓ Patent protection for contributors

### For the Project
- ✓ Enables wider adoption and community contributions
- ✓ Compatible with most other open source licenses
- ✓ Well-understood by legal departments and enterprises
- ✓ Meets open source definition standards

## Files Modified

1. **LICENSE** - Replaced with Apache 2.0 full text
2. **pyproject.toml** - Updated license metadata and classifiers
3. **README.md** - Updated license section
4. **NOTICE** - Created new file (required for Apache 2.0)

## Compliance Notes

To comply with Apache 2.0, derivative works must:
1. Include a copy of the LICENSE file
2. Include the NOTICE file (if present)
3. State significant changes made to the software
4. Preserve all copyright, patent, trademark, and attribution notices

## Additional Resources

- Full license text: [LICENSE](LICENSE)
- Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
- Apache License FAQ: https://www.apache.org/foundation/license-faq.html
