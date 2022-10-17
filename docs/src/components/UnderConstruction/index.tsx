import React from "react";
import Admonition from '@theme/Admonition';


export default function UnderConstruction() {
    return (
        <div>
            <Admonition type="caution" title="注意">
                🚧 当前页文档还在施工中，并未提供完整的使用说明！ 🚧
            </Admonition>
        </div>
    );
}