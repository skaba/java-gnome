/*
 * SetterBlock.java
 *
 * Copyright (c) 2007 Operational Dynamics Consulting Pty Ltd
 * 
 * The code in this file, and the library it is a part of, are made available
 * to you by the authors under the terms of the "GNU General Public Licence,
 * version 2" See the LICENCE file for the terms governing usage and
 * redistribution.
 */
package com.operationaldynamics.defsparser;

import com.operationaldynamics.codegen.Generator;
import com.operationaldynamics.codegen.SetterGenerator;
import com.operationaldynamics.driver.DefsFile;

/**
 * Pseudo Block which is to be created if a field in a (define-boxed ...)
 * block is writable. TODO describe what that looks like, exactly.
 * 
 * @author Andrew Cowie
 * @see GetterBlock
 */
public class SetterBlock extends AccessorBlock
{
    SetterBlock(final String gType, final String name, final String ofObject) {
        super(name, ofObject);

        this.returnType = gType;
    }

    public Generator createGenerator(final DefsFile data) {

        parameters = new String[][] {
                new String[] {
                        addPointerSymbol(ofObject), "self"
                }, new String[] {
                        returnType, blockName
                }
        };

        return new SetterGenerator(data, blockName, parameters);
    }
}
