#
# Codasip s.r.o.
#
# CONFIDENTIAL
#
# Copyright 2019 Codasip s.r.o.
#
# All Rights Reserved.
#
# NOTICE: All information contained in this file, is and shall remain the property of
# Codasip s.r.o. and its suppliers, if any.
#
# The intellectual and technical concepts contained herein are confidential and proprietary to
# Codasip s.r.o. and are protected by trade secret and copyright law.  In addition, elements of the
# technical concepts may be patent pending.
#
# This file is part of the Codasip Studio product. No part of the Studio product, including this
# file, may be use, copied, modified, or distributed except in accordance with the terms contained
# in Codasip license agreement under which you obtained this file.
#


import codasip.tasks as tasks
import codasip.utility.utils


def task_rtl_only(model):
  
    def title(task):
        return "RTL Only"

    return {
        "basename": "rtl_only",
        "actions": [],
        "targets": [],
        "task_dep": ["_rtl_sources"],
        "title": title,
    }
