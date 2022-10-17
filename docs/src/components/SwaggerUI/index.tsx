import BrowserWindow from "@site/src/components/BrowserWindow";
import React from "react";
import styles from './styles.module.css';

interface Props {
    spec: string
    height?: number
}

export default function SwaggerUI({spec, height = 450}: Props) {
    return (
        <BrowserWindow url="http://127.0.0.1:8000/docs/">
            <iframe
                className={styles.iframe}
                style={{height}}
                srcDoc={
                    require('raw-loader!@site/swagger-ui/index.html').default.replace(
                        "'{{spec}}'", JSON.stringify(require(`@site/swagger-ui/spec/${spec}.json`)))
                }>
            </iframe>
        </BrowserWindow>
    )
}
